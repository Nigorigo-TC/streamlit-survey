import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time  # ← リトライ処理に使う

# --- Google Sheets 認証 ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- スプレッドシート設定 ---
SPREADSHEET_NAME = "2025年度_起床時コンディションチェック"
SHEET_NAME = "condition2025"
sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# --- リトライ付き append_row 関数 ---
def safe_append_row(worksheet, row_data, retries=3, delay=1):
    for i in range(retries):
        try:
            worksheet.append_row(row_data)
            return True
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay * (i + 1))  # 1秒→2秒→3秒
            else:
                raise e

# --- スライダー（数値非表示）関数 ---
def secret_slider_with_labels(title, left_label, right_label, key, min_value=0, max_value=100, default=50):
    st.markdown(f"**{title}**")
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between;'>
            <span>{left_label}</span><span>{right_label}</span>
        </div>
    """, unsafe_allow_html=True)
    return st.select_slider("", list(range(min_value, max_value + 1)), default, format_func=lambda x: "", key=key)

# --- アンケート UI ---
st.title("コンディション記録")

st.markdown("**1. 日付**")
date = st.date_input("日付を選択してください")

st.markdown("**2. 所属**")
team = st.text_input("所属")

st.markdown("**3. 名前**")
name = st.text_input("名前")

health_condition = secret_slider_with_labels("4. 全般的体調", "とても悪い", "とても良い", "health")
fatigue = secret_slider_with_labels("5. 疲労感", "とても強い", "全く無い", "fatigue")

st.markdown("**6. 睡眠時間（例：7時間15分→7.25、7時間30分→7.5）**")
sleep_time = st.number_input("", 0.0, 24.0, step=0.1)

sleep_quality = secret_slider_with_labels("7. 睡眠の深さ", "とても浅い", "とても深い", "sleep_quality")

st.markdown("**8. 睡眠状況（複数選択）**")
sleep_issues = st.multiselect("", ["夢を見た", "何回も目覚めた", "何回もトイレに行った", "寝汗をかいた", "普段より寝付けなかった", "特になし"])

appetite = secret_slider_with_labels("9. 食欲", "全く無い", "とてもある", "appetite")

injury = st.radio("**10. 故障の有無**", ["無", "有"])
injury_part = st.text_input("11. 故障の箇所") if injury == "有" else ""

injury_severity = secret_slider_with_labels("12. 故障の程度", "練習できない", "全くない", "injury_severity")
training_intensity = secret_slider_with_labels("13. 練習強度", "非常にきつい", "非常に楽", "training_intensity")

bowel_movement = st.radio("**14. 排便の有無**", ["有", "無"])

st.markdown("**15. 便の形**")
st.image("stool_chart.png", caption="便の形（1～7）", use_container_width=True)
bowel_shape = st.selectbox("該当する番号を選択してください", list(range(1, 8))) if bowel_movement == "有" else ""

running_distance = st.number_input("**16. 走行距離（km）**", 0.0, 100.0, step=0.1)
spo2 = st.number_input("**17. SpO2（％）**", 70, 100)
pulse = st.number_input("**18. 脈拍数（拍/分）**", 30, 200)
temperature = st.number_input("**19. 体温（℃）**", 34.0, 42.0, step=0.1)
weight = st.number_input("**20. 体重（kg）**", 20.0, 150.0, step=0.1)

symptoms = st.multiselect("**21. 特記事項（複数選択）**", [
    "頭痛", "のどの痛み", "鼻水", "咳", "痰", "息苦しさ", "強いだるさ（倦怠感）",
    "臭いがわかりにくい", "味がわかりにくい", "吐き気", "嘔吐", "その他"
])
other_symptoms = st.text_input("21-1. その他の症状") if "その他" in symptoms else ""

exercise_time = st.number_input("**22. トレーニング時間（分）**", 0, 300)

st.markdown("**23. 運動のきつさ（RPE）**")
st.image("rpe_chart.png", caption="運動のきつさ（0～10）", use_container_width=True)
exercise_rpe = st.selectbox("RPEを選択してください", list(range(0, 11)))

# --- 送信処理（リトライ付き） ---
# Google Sheets の読み込みを送信ボタンの中に移動！
if st.button("送信"):
    if not team or not name:
        st.error("❗ 所属と名前を入力してください")
    elif not sleep_issues:
        st.error("❗ 8. 睡眠状況を選んでください")
    elif injury == "有" and not injury_part:
        st.error("❗ 11. 故障の箇所を入力してください")
    elif "その他" in symptoms and not other_symptoms:
        st.error("❗ 21-1. その他の症状を入力してください")
    elif exercise_rpe is None:
        st.error("❗23. 運動のきつさ（RPE）を選択してください")
    else:
        try:
            # ここで初めて Sheets に接続！
            sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
            safe_append_row(sheet, [
                str(date), team, name, health_condition, fatigue,
                sleep_time, sleep_quality, ", ".join(sleep_issues),
                appetite, injury, injury_part, injury_severity,
                training_intensity, bowel_movement, bowel_shape,
                running_distance, spo2, pulse, temperature, weight,
                ", ".join(symptoms), other_symptoms,
                exercise_time, exercise_rpe
            ])
            st.success("✅ Googleスプレッドシートに送信しました！")
        except Exception as e:
            st.error(f"送信失敗（リトライ後）: {e}")

