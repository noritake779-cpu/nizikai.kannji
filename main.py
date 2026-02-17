import streamlit as st
import pandas as pd
import os

# --- 1. 基本設定 ---
CSV_FILE = 'attendance_data.csv'
PRICE_ADULT = 5000
PRICE_CHILD = 1500
PRICE_TEACHER = 2000

st.set_page_config(page_title="二次会幹事くん", layout="wide")

# --- 2. データの読み込み（古い列を強制排除） ---
def load_data():
    # 正しい列の定義（名前、大人、子供、先生、集金済、備考）
    target_cols = ['名前', '大人', '子供', '先生', '集金済', '備考']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # 【重要】以前の「家庭合計」など、設定にない列がCSVにあると即エラーになるため、
            # 必要な列だけを「選別」して取り出します。
            valid_cols = [c for c in target_cols if c in df.columns]
            df = df[valid_cols].copy()
            
            # 足りない列（先生など）を補完
            for col in target_cols:
                if col not in df.columns:
                    if col == '集金済': df[col] = False
                    elif col in ['大人', '子供', '先生']: df[col] = 0
                    else: df[col] = ""
            
            # データ型を固定（ここがズレるとチェックボックスが出ません）
            df['大人'] = pd.to_numeric(df['大人'], errors='coerce').fillna(0).astype(int)
            df['子供'] = pd.to_numeric(df['子供'], errors='coerce').fillna(0).astype(int)
            df['先生'] = pd.to_numeric(df['先生'], errors='coerce').fillna(0).astype(int)
            df['集金済'] = df['集金済'].astype(bool)
            
            return df[target_cols]
        except:
            pass

    # 初期サンプルデータ
    return pd.DataFrame({
        '名前': ['森本', '廣川', '山崎', '宮田', '田島', '高橋'],
        '大人': [1, 2, 2, 2, 0, 2],
        '子供': [1, 2, 1, 2, 0, 2],
        '先生': [0, 0, 0, 0, 0, 0],
        '集金済': [False] * 6,
        '備考': [""] * 6
    })

# メモリ上のデータを初期化
if 'df_final_fixed' not in st.session_state:
    st.session_state.df_final_fixed = load_data()

st.title("二次会 出欠・集金管理")

# --- 3. メイン編集エリア ---
st.subheader("📝 ゲストリスト編集")
st.info("一番下の空行に名前を入れると、自動でチェックボックスや0が追加されます。")

# 【最重要】keyを全く新しいもの（teacher_mode_v1）に変更しました。
# これにより、Streamlit Cloud上の古いキャッシュを強制的に破棄します。
edited_df = st.data_editor(
    st.session_state.df_final_fixed,
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
    key="teacher_mode_v1" 
)

# 保存ボタン
if st.button("💾 データを保存する"):
    st.session_state.df_final_fixed = edited_df
    # CSVには計算用の列を含めず、純粋なデータのみ保存
    edited_df.to_csv(CSV_FILE, index=False)
    st.success("保存が完了しました！")
    st.rerun()

# --- 4. 会計状況の集計 ---
calc_df = edited_df.copy()
# 金額計算（大人5000、子供1500、先生2000）
calc_df['小計'] = (calc_df['大人'].astype(int) * PRICE_ADULT) + \
                 (calc_df['子供'].astype(int) * PRICE_CHILD) + \
                 (calc_df['先生'].astype(int) * PRICE_TEACHER)

st.divider()
st.subheader("📊 会計状況")

total_money = calc_df['小計'].sum()
paid_money = calc_df[calc_df['集金済'] == True]['小計'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("総人数", f"{int(calc_df[['大人', '子供', '先生']].sum().sum())} 名")
c2.metric("総売上予定", f"¥{int(total_money):,}")
c3.metric("回収済金額", f"¥{int(paid_money):,}", f"不足 ¥{int(total_money - paid_money):,}", delta_color="inverse")

# 計算結果を含めた表の表示
st.dataframe(
    calc_df[['名前', '大人', '子供', '先生', '小計', '集金済', '備考']],
    column_config={"小計": st.column_config.NumberColumn(format="¥%d")},
    use_container_width=True
)

# --- 5. 印刷用 ---
if st.checkbox("🖨️ PDF・印刷用リストを表示"):
    print_df = calc_df.copy()
    print_df['集金済'] = print_df['集金済'].apply(lambda x: "済" if x else " ")
    st.table(print_df[['名前', '大人', '子供', '先生', '小計', '集金済', '備考']])
