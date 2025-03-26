import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets API 認証（secrets.toml 経由）
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# スプレッドシート設定
SPREADSHEET_NAME = "2025年度_起床時コンディションチェック"
SHEET_NAME = "condition2025"
worksheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

# スライダー（数値非表示）関数
def secret_slider_with_labels(title, left_label, right_label, key, min_value=0, max_value=100, default=50):
    st.markdown(f"**{title}**")
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between;'>
            <span>{left_label}</span><span>{right_label}</span>
        </div>
    """, unsafe_allow_html=True)
    return st.select_slider(
        label="",
        options=list(range(min_value, max_value + 1)),
        value=default,
        format_func=lambda x: "",
        key=key
    )

# UI ---------------------
st.title("コンディション記録アンケート")

st.markdown("**1. 日付**")
date = st.date_input("日付を選択してください")

st.markdown("**2. 所属**")
team = st.text_input("所属")

st.markdown("**3. 名前**")
name = st.text_input("名前")

health_condition = secret_slider_with_labels("4. 全般的体調", "とても悪い", "とても良い", key="health")
fatigue = secret_slider_with_labels("5. 疲労感", "とても強い", "全く無い", key="fatigue")

st.markdown("**6. 睡眠時間（例：7.5）**")
sleep_time = st.number_input("", min_value=0.0, max_value=24.0, step=0.1)

sleep_quality = secret_slider_with_labels("7. 睡眠の深さ", "とても浅い", "とても深い", key="sleep_quality")

st.markdown("**8. 睡眠状況（複数選択）**")
sleep_issues = st.multiselect("", [
    "夢を見た", "何回も目覚めた", "何回もトイレに行った", "寝汗をかいた", "普段より寝付けなかった", "特になし"
])

appetite = secret_slider_with_labels("9. 食欲", "全く無い", "とてもある", key="appetite")

st.markdown("**10. 故障の有無**")
injury = st.radio("", ["無", "有"])

st.markdown("**11. 故障の箇所**")
injury_part = st.text_input("") if injury == "有" else ""

injury_severity = secret_slider_with_labels("12. 故障の程度", "練習できない", "全くない", key="injury_severity")
training_intensity = secret_slider_with_labels("13. 練習強度", "非常にきつい", "非常に楽", key="training_intensity")

st.markdown("**14. 排便の有無**")
bowel_movement = st.radio("", ["有", "無"])

st.markdown("**15. 便の形**")
st.image("stool_chart.png", caption="便の形（1～7）", use_column_width=True)
bowel_shape = st.selectbox("15-1. 該当する番号を選択してください", list(range(1, 8))) if bowel_movement == "有" else ""

st.markdown("**16. 走行距離（km）**")
running_distance = st.number_input("", 0.0, 100.0, step=0.1)

st.markdown("**17. SpO2（％）**")
spo2 = st.number_input("", 70, 100)

st.markdown("**18. 脈拍数（拍/分）**")
pulse = st.number_input("", 30, 200)

st.markdown("**19. 体温（℃）**")
temperature = st.number_input("", 34.0, 42.0, step=0.1)

st.markdown("**20. 体重（kg）**")
weight = st.number_input("", 20.0, 150.0, step=0.1)

st.markdown("**21. 特記事項（複数選択）**")
symptoms = st.multiselect("", [
    "頭痛", "のどの痛み", "鼻水", "咳", "痰", "息苦しさ", "強いだるさ（倦怠感）",
    "臭いがわかりにくい", "味がわかりにくい", "吐き気", "嘔吐", "その他"
])
other_symptoms = st.text_input("21-1. その他の症状") if "その他" in symptoms else ""

st.markdown("**22. トレーニング時間（分）**")
exercise_time = st.number_input("", 0, 300)

st.markdown("**23. 運動のきつさ（RPE）**")
st.image("rpe_chart.png", caption="運動のきつさ（0～10）", use_column_width=True)
exercise_rpe = st.selectbox("23-1. RPEを選択してください", list(range(0, 11)))


# 送信処理 ---------------------
if st.button("送信"):
    try:
        worksheet.append_row([
            str(date),
            team,
            name,
            health_condition,
            fatigue,
            sleep_time,
            sleep_quality,
            ", ".join(sleep_issues),
            appetite,
            injury,
            injury_part,
            injury_severity,
            training_intensity,
            bowel_movement,
            bowel_shape,
            running_distance,
            spo2,
            pulse,
            temperature,
            weight,
            ", ".join(symptoms),
            other_symptoms,
            exercise_time,
            exercise_rpe
        ])
        st.success("Googleスプレッドシートに送信しました！")
    except Exception as e:
        st.error(f"送信失敗: {e}")