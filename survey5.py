import streamlit as st
import requests
from datetime import date

# --- Supabase 接続情報 ---
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE_NAME = "condition2025"

def submit_to_supabase(data_dict):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        json=[data_dict],  # ★ Supabaseはリスト形式で受け取る
        headers=headers
    )
    return response.status_code == 201

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

date = st.date_input("**1. 日付**", value=date.today())
team = st.text_input("**2. 所属**")
name = st.text_input("**3. 名前**")

health_condition = secret_slider_with_labels("4. 全般的体調", "とても悪い", "とても良い", "health")
fatigue = secret_slider_with_labels("5. 疲労感", "とても強い", "全く無い", "fatigue")
sleep_time = st.number_input("**6. 睡眠時間（例：7.5）**", 0.0, 24.0, step=0.1)
sleep_quality = secret_slider_with_labels("7. 睡眠の深さ", "とても浅い", "とても深い", "sleep_quality")

sleep_issues = st.multiselect("**8. 睡眠状況（複数選択）**", [
    "夢を見た", "何回も目覚めた", "何回もトイレに行った", "寝汗をかいた", "普段より寝付けなかった", "特になし"
])

appetite = secret_slider_with_labels("9. 食欲", "全く無い", "とてもある", "appetite")
injury = st.radio("**10. 故障の有無**", ["無", "有"])
injury_part = st.text_input("11. 故障の箇所") if injury == "有" else ""

injury_severity = secret_slider_with_labels("12. 故障の程度", "練習できない", "全くない", "injury_severity")
training_intensity = secret_slider_with_labels("13. 練習強度", "非常にきつい", "非常に楽", "training_intensity")

bowel_movement = st.radio("**14. 排便の有無**", ["有", "無"])
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
st.image("rpe_chart.png", caption="運動のきつさ（0～10）", use_container_width=True)
exercise_rpe = st.selectbox("RPEを選択してください", list(range(0, 11)))

# --- 送信処理 ---
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
        data = {
            "date": str(date),
            "team": team,
            "name": name,
            "health": health_condition,
            "fatigue": fatigue,
            "sleep_time": sleep_time,
            "sleep_quality": sleep_quality,
            "sleep_issues": ", ".join(sleep_issues),
            "appetite": appetite,
            "injury": injury,
            "injury_part": injury_part,
            "injury_severity": injury_severity,
            "training_intensity": training_intensity,
            "bowel_movement": bowel_movement,
            "bowel_shape": bowel_shape,
            "running_distance": running_distance,
            "spo2": spo2,
            "pulse": pulse,
            "temperature": temperature,
            "weight": weight,
            "symptoms": ", ".join(symptoms),
            "other_symptoms": other_symptoms,
            "exercise_time": exercise_time,
            "exercise_rpe": exercise_rpe
        }

        if submit_to_supabase(data):
            st.success("✅ Supabaseに送信しました！")
        else:
            st.error("❌ Supabaseへの送信に失敗しました。")
