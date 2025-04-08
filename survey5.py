import streamlit as st
import requests
from datetime import date
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Supabase 接続情報 ---
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
TABLE_NAME = "condition"

# --- Supabaseにデータ送信 ---
def submit_to_supabase(data_dict):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    data_dict["exported"] = False  # 新規は未出力とする
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        json=[data_dict],
        headers=headers
    )
    return response.status_code == 201

# --- Supabaseから未出力データ取得 ---
def fetch_unexported_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?exported=eq.false&select=*"
    res = requests.get(url, headers=headers)
    return pd.DataFrame(res.json())

# --- Supabaseのデータをexported=trueに更新 ---
def mark_as_exported(ids):
    if not ids:
        return
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    for record_id in ids:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{record_id}"
        requests.patch(url, headers=headers, json={"exported": True})

# --- Googleスプレッドシート出力 ---
SPREADSHEET_NAME = "2025年度_起床時コンディションチェック"
SHEET_NAME = "condition2025"

def export_to_gsheet(df):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

    existing_data = sheet.get_all_values()
    if not existing_data:
        sheet.insert_row(df.columns.tolist(), 1)  # ヘッダーがない場合のみ追加

    sheet.append_rows(df.values.tolist())

# --- スライダー（数値非表示）関数 ---
def secret_slider_with_labels(title, left_label, right_label, key, min_value=0, max_value=100, default=50):
    st.markdown(f"**{title}**")
    value = st.select_slider("", list(range(min_value, max_value + 1)), default, format_func=lambda x: "", key=key)
    st.markdown(f"<div style='display: flex; justify-content: space-between;'><span>{left_label}</span><span>{right_label}</span></div>", unsafe_allow_html=True)
    return value

# --- 送信完了フラグ初期化 ---
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# --- 管理者判定 ---
query_params = st.query_params
is_admin = query_params.get("admin", ["0"])[0] == "1"

# ========================
# 管理者ページ（?admin=1）
# ========================
if is_admin:
    st.title("🛠 管理者メニュー（未出力データ → スプレッドシート）")
    admin_pass = st.text_input("管理者パスワードを入力", type="password", key="admin_password_input")

    if admin_pass == st.secrets.get("admin_password"):
        if st.button("📤 未出力データを出力する"):
            df = fetch_unexported_data()
            if df.empty:
                st.warning("⚠ 未出力データはありません")
            else:
                export_to_gsheet(df.drop(columns=["exported"]))
                mark_as_exported(df["id"].tolist())
                st.success(f"✅ {len(df)} 件のデータを出力し、exported=true に更新しました！")
    elif admin_pass:
        st.error("❌ パスワードが間違っています")
        
# ========================
# 一般ユーザー用ページ
# ========================
if not is_admin:
    st.title("Record of the physical condition")

    if not st.session_state["submitted"]:
        date_val = st.date_input("**1. Date**", value=date.today(), key="date")
        st.caption("")

        st.markdown("**2. Team name**")
        team = st.text_input("", key="team")
        st.caption("")

        st.markdown("**3. Name**")
        name = st.text_input("", key="name")
        st.caption("※ Please write your fulname")

        health_condition = secret_slider_with_labels("4. Body condition", "Very Bad", "Very Good", "health")
        st.caption("")

        fatigue = secret_slider_with_labels("5. Fatigue", "Very Bad", "Very Good", "fatigue")
        st.caption("")

        st.markdown("**6. Amout of sleep（ex. 7h15min→7.25、7h30min→7.5）**")
        sleep_time = st.number_input("", 0.0, 24.0, step=0.1, key="sleep_time")
        st.caption("")

        sleep_quality = secret_slider_with_labels("7. Deepness of sleep", "Very Shallow", "Very Deep", "sleep_quality")
        st.caption("")

        st.markdown("**8. Quality of sleep（multiple choice）**")
        sleep_issues = st.multiselect("", [
            "Had a dream", "Woke up many times", "Went to restroom many times", "Perspired in sleep", "uneasy", "特になし"], key="sleep_issues")
        st.caption("")

        appetite = secret_slider_with_labels("9. 食欲", "全く無い", "とてもある", "appetite")
        st.caption("")

        injury = st.radio("**10. 故障の有無**", ["無", "有"], key="injury")
        st.caption("")

        st.markdown("**11. 故障の箇所**")
        injury_part = st.text_input("", key="injury_part") if injury == "有" else ""
        st.caption("※ 故障している場合は部位を具体的に入力")

        injury_severity = secret_slider_with_labels("12. 故障の程度", "練習できない", "全くない", "injury_severity")
        st.caption("")

        training_intensity = secret_slider_with_labels("13. 練習強度", "非常にきつい", "非常に楽", "training_intensity")
        st.caption("")

        bowel_movement = st.radio("**14. 排便の有無**", ["有", "無"], key="bowel_movement")
        st.caption("")

        st.image("stool_chart.png", caption="便の形（1～7）", use_container_width=True)

        st.markdown("**15. 便の形**")
        bowel_shape = st.selectbox("該当する番号を選択してください", list(range(1, 8)), key="bowel_shape") if bowel_movement == "有" else ""
        st.caption("※ 画像を参考に選択")

        running_distance = st.number_input("**16. 走行距離（km）**", 0.0, 100.0, step=0.1, key="running_distance")
        st.caption("")

        spo2 = st.number_input("**17. SpO2（％）**", 70, 100, key="spo2")
        st.caption("")

        pulse = st.number_input("**18. 脈拍数（拍/分）**", 30, 200, key="pulse")
        st.caption("")

        temperature = st.number_input("**19. 体温（℃）**", 34.0, 42.0, step=0.1, key="temperature")
        st.caption("")

        weight = st.number_input("**20. 体重（kg）**", 20.0, 150.0, step=0.1, key="weight")
        st.caption("")

        symptoms = st.multiselect("**21. 特記事項（複数選択）**", [
            "頭痛", "のどの痛み", "鼻水", "咳", "痰", "息苦しさ", "強いだるさ（倦怠感）",
            "臭いがわかりにくい", "味がわかりにくい", "吐き気", "嘔吐", "その他"], key="symptoms")
        st.caption("")

        other_symptoms = st.text_input("21-1. その他の症状", key="other_symptoms") if "その他" in symptoms else ""
        if "その他" in symptoms:
            st.caption("")

        exercise_time = st.number_input("**22. トレーニング時間（分）**", 0, 300, key="exercise_time")
        st.caption("")

        st.image("rpe_chart.png", caption="運動のきつさ（0～10）", use_container_width=True)
        exercise_rpe = st.selectbox("**23. 運動のきつさ（RPE）**", list(range(0, 11)), key="exercise_rpe")
        st.caption("※画像を参考に運動のきつさ（RPE）を選択してください")

        if st.button("送信"):
            if not team or not name:
                st.error("❗ 所属と名前を入力してください")
            elif not sleep_issues:
                st.error("❗ 8. 睡眠状況を選んでください")
            elif injury == "有" and not injury_part:
                st.error("❗ 11. 故障の箇所を入力してください")
            elif "その他" in symptoms and not other_symptoms:
                st.error("❗ 21-1. その他の症状を入力してください")
            elif not exercise_rpe:
                st.error("❗23. 運動のきつさ（RPE）を選択してください")
            else:
                data = {
                    "date": str(date_val), "team": team, "name": name,
                    "health": health_condition, "fatigue": fatigue,
                    "sleep_time": sleep_time, "sleep_quality": sleep_quality,
                    "sleep_issues": ", ".join(sleep_issues), "appetite": appetite,
                    "injury": injury, "injury_part": injury_part,
                    "injury_severity": injury_severity, "training_intensity": training_intensity,
                    "bowel_movement": bowel_movement, "bowel_shape": bowel_shape,
                    "running_distance": running_distance, "spo2": spo2, "pulse": pulse,
                    "temperature": temperature, "weight": weight,
                    "symptoms": ", ".join(symptoms), "other_symptoms": other_symptoms,
                    "exercise_time": exercise_time, "exercise_rpe": exercise_rpe
                }
                if submit_to_supabase(data):
                    st.session_state["submitted"] = True
                    st.rerun()
                else:
                    st.error("❌ Supabaseへの送信に失敗しました。")
    else:
        st.success("✅ 回答ありがとうございました！")
        st.balloons()
        st.markdown("次回もよろしくお願いします！")

