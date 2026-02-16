import streamlit as st
import pandas as pd
import os

# --- 1. 基本設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 2. データの強制初期化・読み込み ---
def load_data():
    # 必要な列を定義
    cols = ['名前', '大人', '子供', '先生', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # 必要な列だけを残す（エラー対策の外科手術）
            df = df[[c for c in cols if c in df.columns]].copy()
            # 足りない列を補う
            for c in cols:
                if c not in df.columns:
                    df[c] = False if c == '集金済' else 0 if c in ['大人', '子供', '先生'] else ""
            return df[cols]
        except:
            pass

    # 初期サンプルデータ
    return pd.DataFrame([
        {'名前': '森本', '大人': 1, '子供': 1, '先生': 0, '集金済': False, '備考': ''},
        {'名前': '廣川', '大人': 2, '子供': 2, '先生': 0, '集金済': False, '備考': ''},
    ])

# セッション状態にデータを保持
if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("二次会 出欠・集金管理")

# --- 3. メイン編集エリア ---
st.subheader("📝 ゲストリスト編集")
st.info("一番下の空行に名前を入力すると、自動でチェックボックスや0が追加されます。")

# エディタ（最もエラーが起きにくいシンプルな設定）
edited_df = st.data_editor(
    st.session_state.df,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0, step=1, default=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0, step=1, default=0),
        "先生": st.column_config.NumberColumn("先生", min_value=0, step=1, default=0),
        "集金済": st.column_config.CheckboxColumn("集金済", default=False),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_final_ver" # 以前とキーを変えてキャッシュをリセット
)

# 保存ボタン
if st.button("💾 変更を保存する"):
    st.session_state.df = edited_df
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存に成功しました！")
    st.rerun()

# --- 4. 集計表示 ---
calc_df = edited_df.copy()
# 計算（新規行も即反映）
calc_df['合計金額'] = (calc_df['大人'] * PRICE_ADULT) + \
                      (calc_df['子供'] * PRICE_CHILD) + \
                      (calc_df['先生'] * PRICE_TEACHER)

st.divider()
st.subheader("📊 会計・集計")

total_money = calc_df['合計金額'].sum()
paid_money = calc_df[calc_df['集金済'] == True]['合計金額'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{int(calc_df[['大人', '子供', '先生']].sum().sum())}名")
m2.metric("売上予定", f"¥{int(total_money):,}")
m3.metric("回収済", f"¥{int(paid_money):,}", f"不足 ¥{int(total_money - paid_money):,}", delta_color="inverse")

# 金額入り確認表
st.dataframe(calc_df, use_container_width=True)

# --- 5. 印刷用（PDFの代わり） ---
st.divider()
if st.checkbox("🖨️ 印刷用リストを表示"):
    st.write("この表が表示されたら、スマホやPCのブラウザメニューから『印刷』を選び、PDFとして保存してください。")
    print_tab = calc_df.copy()
    print_tab['集金済'] = print_tab['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_tab)
