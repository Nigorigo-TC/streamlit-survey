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
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        json=[data_dict],
        headers=headers
    )
    return response.status_code == 201

# --- Supabaseから全データ取得（管理者用） ---
def fetch_supabase_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    res = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=headers)
    return pd.DataFrame(res.json())

# --- Googleスプレッドシート出力（管理者用） ---
SPREADSHEET_NAME = "2025年度_起床時コンディションチェック"
SHEET_NAME = "condition2025"

def export_to_gsheet(df):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    sheet.clear()
    sheet.insert_row(df.columns.tolist(), 1)
    sheet.insert_rows(df.values.tolist(), 2)

# --- スライダー（数値非表示）関数 ---
def secret_slider_with_labels(title, left_label, right_label, key, min_value=0, max_value=100, default=50):
    st.markdown(f"**{title}**")
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between;'>
            <span>{left_label}</span><span>{right_label}</span>
        </div>
    """, unsafe_allow_html=True)
    return st.select_slider("", list(range(min_value, max_value + 1)), default, format_func=lambda x: "", key=key)

# --- 送信完了フラグ初期化 ---
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

# --- 管理者判定 ---
query_params = st.query_params
is_admin = query_params.get("admin", ["0"])[0] == "1"

# ========================
# 一般ユーザー用ページ
# ========================
if not is_admin:
    st.title("コンディション記録")

    if not st.session_state["submitted"]:
        date_val = st.date_input("**1. 日付**", value=date.today())
        st.caption("※ 本日の日付を選択してください")
        st.text_input("備考 (1. 日付)")

        st.markdown("**2. 所属**")
        st.caption("※ チーム名や学校名など")
        team = st.text_input("")
        st.text_input("備考 (2. 所属)")

        st.markdown("**3. 名前**")
        st.caption("※ フルネームで入力してください")
        name = st.text_input("")
        st.text_input("備考 (3. 名前)")

        st.caption("※ 起床時の体調を主観的に評価してください")
        health_condition = secret_slider_with_labels("4. 全般的体調", "とても悪い", "とても良い", "health")
        st.text_input("備考 (4. 全般的体調)")

        st.caption("※ 身体的な疲労感を評価してください")
        fatigue = secret_slider_with_labels("5. 疲労感", "とても強い", "全く無い", "fatigue")
        st.text_input("備考 (5. 疲労感)")

        st.markdown("**6. 睡眠時間（例：7.5）**")
        st.caption("※ 小数点で入力（例：7時間30分 → 7.5）")
        sleep_time = st.number_input("", 0.0, 24.0, step=0.1)
        st.text_input("備考 (6. 睡眠時間)")

        st.caption("※ 寝つき・途中覚醒の少なさなどから主観的に評価")
        sleep_quality = secret_slider_with_labels("7. 睡眠の深さ", "とても浅い", "とても深い", "sleep_quality")
        st.text_input("備考 (7. 睡眠の深さ)")

        st.markdown("**8. 睡眠状況（複数選択）**")
        st.caption("※ 複数当てはまる場合はすべて選んでください")
        sleep_issues = st.multiselect("", [
            "夢を見た", "何回も目覚めた", "何回もトイレに行った", "寝汗をかいた", "普段より寝付けなかった", "特になし"])
        st.text_input("備考 (8. 睡眠状況)")

        st.caption("※ 朝食時の食欲の度合い")
        appetite = secret_slider_with_labels("9. 食欲", "全く無い", "とてもある", "appetite")
        st.text_input("備考 (9. 食欲)")

        injury = st.radio("**10. 故障の有無**", ["無", "有"])
        st.text_input("備考 (10. 故障の有無)")

        st.markdown("**11. 故障の箇所**")
        st.caption("※ 故障している場合は部位を具体的に入力")
        injury_part = st.text_input("") if injury == "有" else ""
        st.text_input("備考 (11. 故障の箇所)")

        st.caption("※ 故障が練習にどの程度影響しているか")
        injury_severity = secret_slider_with_labels("12. 故障の程度", "練習できない", "全くない", "injury_severity")
        st.text_input("備考 (12. 故障の程度)")

        st.caption("※ 昨日の練習がどれくらいきつかったか")
        training_intensity = secret_slider_with_labels("13. 練習強度", "非常にきつい", "非常に楽", "training_intensity")
        st.text_input("備考 (13. 練習強度)")

        st.caption("※ 昨日の排便の有無")
        bowel_movement = st.radio("**14. 排便の有無**", ["有", "無"])
        st.text_input("備考 (14. 排便の有無)")

        st.image("stool_chart.png", caption="便の形（1～7）", use_container_width=True)

        st.markdown("**15. 便の形**")

        if st.button("送信"):
            if not team or not name:
                st.error("❗ 所属と名前を入力してください")
            elif not sleep_issues:
                st.error("❗ 8. 睡眠状況を選んでください")
            elif injury == "有" and not injury_part:
                st.error("❗ 11. 故障の箇所を入力してください")
            elif "その他" in symptoms and not other_symptoms:
                st.error("❗ 21-1. その他の症状を入力してください")
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

# ========================
# 管理者ページ（?admin=1）
# ========================
else:
    st.title("🛠 管理者メニュー（Supabase → スプレッドシート出力）")
    admin_pass = st.text_input("管理者パスワードを入力", type="password")
    if admin_pass == st.secrets.get("admin_password"):
        if st.button("📤 データを出力する"):
            df = fetch_supabase_data()
            if df.empty:
                st.warning("⚠ Supabaseにデータがありません")
            else:
                export_to_gsheet(df)
                st.success(f"✅ {len(df)} 件のデータをGoogleスプレッドシートに出力しました！")
    elif admin_pass:
        st.error("❌ パスワードが間違っています")
