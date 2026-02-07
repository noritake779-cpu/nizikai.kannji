import streamlit as st
import pandas as pd
import os

# --- 設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 【重要】データ修復・読み込みロジック ---
def get_safe_data():
    valid_cols = ['名前', '大人', '子供', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            raw_df = pd.read_csv(CSV_FILE)
            # エラーの原因となる「家庭合計」列が混じっていたら強制削除
            safe_df = raw_df[[c for c in valid_cols if c in raw_df.columns]].copy()
            
            # 足りない列があれば補完
            for c in valid_cols:
                if c not in safe_df.columns:
                    safe_df[c] = False if c == '集金済' else (0 if c in ['大人', '子供'] else "")
            
            # もしこの時点で空っぽ（列が一つもない）なら初期データを返す
            if safe_df.empty or len(safe_df.columns) < 2:
                raise ValueError("Data is corrupted")
                
            return safe_df
        except:
            # CSVが壊れている、または古い形式の場合は初期データを生成
            pass

    # 初期データ（画像に基づいたサンプル）
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# データのロード
# 起動時に一度だけ安全なデータをセッションに格納
if 'df_main' not in st.session_state:
    st.session_state.df_main = get_safe_data()

st.title("二次会 出欠・集金管理")

# --- 1. 編集セクション ---
st.subheader("📝 ゲストリスト編集・集金チェック")

# 計算列を絶対に含ませないようにエディタを表示
edited_df = st.data_editor(
    st.session_state.df_main,
    column_config={
        "名前": st.column_config.TextColumn("名前"),
        "大人": st.column_config.NumberColumn("大人", min_value=0),
        "子供": st.column_config.NumberColumn("子供", min_value=0),
        "集金済": st.column_config.CheckboxColumn("集金済"),
        "備考": st.column_config.TextColumn("備考"),
    },
    num_rows="dynamic",
    use_container_width=True,
    key="editor_final" # キーを変更して内部キャッシュをクリア
)

# 保存処理
if st.button("💾 変更を保存する"):
    st.session_state.df_main = edited_df
    # CSVには計算用の「家庭合計」を含めず、純粋な5列のみ保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存完了！")
    st.rerun()

# --- 2. 表示・集計セクション ---
# ここで初めて「表示用」として計算を行う
display_df = edited_df.copy()
display_df['家庭合計'] = (display_df['大人'] * PRICE_ADULT) + (display_df['子供'] * PRICE_CHILD)

st.divider()
st.subheader("💰 会計状況")

t_money = display_df['家庭合計'].sum()
c_money = display_df[display_df['集金済'] == True]['家庭合計'].sum()

m1, m2, m3 = st.columns(3)
m1.metric("総人数", f"{display_df['大人'].sum() + display_df['子供'].sum()}名")
m2.metric("総売上予定", f"¥{t_money:,}")
m3.metric("回収済", f"¥{c_money:,}", f"不足 ¥{t_money - c_money:,}", delta_color="inverse")

# 金額入りの確認用テーブル
st.dataframe(display_df, use_container_width=True)

# --- 3. 印刷用プレビュー ---
st.divider()
if st.checkbox("🖨️ 印刷・PDF用プレビューを表示"):
    st.info("ブラウザの「印刷」メニューからPDF保存してください。")
    # 印刷用に「集金済」を文字に変える
    print_df = display_df[['名前', '大人', '子供', '家庭合計', '集金済', '備考']].copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df)
