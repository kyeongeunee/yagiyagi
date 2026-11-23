import glob
import os
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta
from urllib.parse import unquote

import pandas as pd
import requests
import streamlit as st

# ==========================================================
# 1. 여기에 공공데이터포털 일반 인증키(Decoding)를 붙여넣으세요
#    (배포 시에는 GitHub 대신 Streamlit Cloud Secrets의 PUBLIC_DATA_KEY 권장)
# ==========================================================
DEFAULT_API_KEY = ""


def get_configured_api_key() -> str:
    try:
        secret_val = st.secrets.get("PUBLIC_DATA_KEY", "")
        if secret_val and str(secret_val).strip():
            return str(secret_val).strip()
    except Exception:
        pass
    return DEFAULT_API_KEY.strip()


st.set_page_config(
    page_title="야기야기 | 스마트 복약·유통기한·DUR 관리",
    page_icon="💊",
    layout="centered",
)

# ==========================================================
# 2. 모바일 앱 스타일 커스텀 CSS (야기야기 민트-블루 테마)
# ==========================================================
st.markdown(
    """
    <style>
    .block-container {
        max-width: 560px !important;
        padding-top: 2.6rem !important;
        padding-bottom: 4rem !important;
    }
    div[data-testid="stRadio"] > div {
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        overflow: visible !important;
    }
    div[data-testid="stRadio"] label {
        line-height: 1.4 !important;
        white-space: nowrap !important;
    }
    .yagiyagi-brand {
        color: #4EA898;
        font-weight: 800;
        font-size: 0.95rem;
        margin-bottom: 0.1rem;
    }
    .yagiyagi-title {
        color: #111827;
        font-weight: 800;
        font-size: 1.75rem;
        margin-top: 0;
        margin-bottom: 1.1rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #52A896 0%, #5B89C7 100%);
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        color: #FFFFFF;
        box-shadow: 0 10px 24px rgba(82, 168, 150, 0.22);
        margin-bottom: 1.2rem;
    }
    .hero-grid {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-col { width: 48%; }
    .hero-divider {
        width: 1px;
        height: 54px;
        background: rgba(255, 255, 255, 0.35);
    }
    .hero-label { font-size: 0.85rem; opacity: 0.92; margin-bottom: 0.25rem; }
    .hero-num { font-size: 2rem; font-weight: 800; line-height: 1.1; }
    .hero-num span { font-size: 1rem; font-weight: 600; margin-left: 2px; }
    .hero-sub { margin-top: 0.9rem; font-size: 0.78rem; opacity: 0.88; }
    .empty-card {
        background: #FFFFFF;
        border: 1px solid #EEF2F6;
        border-radius: 20px;
        padding: 2.6rem 1.5rem 2.2rem 1.5rem;
        text-align: center;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
    }
    .mint-guide-box {
        background: #E7F4F1;
        border-radius: 14px;
        padding: 0.95rem 1.1rem;
        color: #1F2937;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 0.9rem;
    }
    .ai-guide-card {
        background: #EEF6FF;
        border-left: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        color: #1E3A8A;
        font-size: 0.87rem;
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }
    .supp-warn-card {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        color: #78350F;
        font-size: 0.87rem;
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }
    .med-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
        margin-bottom: 0.75rem;
    }
    .badge-mint {
        display: inline-block; background: #E6F4F1; color: #2F7E6E;
        font-weight: 700; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px;
    }
    .badge-warn {
        display: inline-block; background: #FEF3C7; color: #B45309;
        font-weight: 700; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px;
    }
    .badge-danger {
        display: inline-block; background: #FEE2E2; color: #B91C1C;
        font-weight: 700; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px;
    }
    .timeline-row {
        display: flex; align-items: flex-start; gap: 14px;
        padding: 0.65rem 0; border-left: 2px solid #D5EAE5;
        margin-left: 18px; padding-left: 22px; position: relative;
    }
    .timeline-dot {
        position: absolute; left: -19px; top: 8px; width: 36px; height: 36px;
        border-radius: 50%; background: linear-gradient(135deg, #54A597, #5B8EC4);
        color: white; display: flex; align-items: center; justify-content: center;
        font-size: 1rem; box-shadow: 0 4px 10px rgba(84, 165, 151, 0.25);
    }
    .disclaimer-box {
        background: #F3F6F9; border-radius: 12px; padding: 0.85rem 1rem;
        color: #64748B; font-size: 0.8rem; margin-top: 1.2rem;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #52A896 0%, #5896B5 100%) !important;
        border: none !important; color: white !important; font-weight: 700 !important;
        border-radius: 14px !important; padding: 0.6rem 1.2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

RX_SLOT_OPTIONS = [
    "아침·점심·저녁 식후 30분",
    "아침·점심·저녁 식후 직후",
    "아침·점심·저녁 식전",
    "아침·저녁 식후 30분",
    "아침·저녁 식후 직후",
    "아침·저녁 식전",
    "아침 식후 30분",
    "아침 식후 직후",
    "아침 식전",
    "점심 식후 30분",
    "점심 식후 직후",
    "점심 식전",
    "저녁 식후 30분",
    "저녁 식후 직후",
    "저녁 식전",
    "기상 직후 (공복)",
    "취침 전",
]


# ==========================================================
# 3. 로컬 DUR 병용금기 CSV 로더 & 성분 사전 구축
# ==========================================================
@st.cache_data(show_spinner="식약처 DUR 병용금기 데이터 로드 중...")
def load_dur_csv():
    target_files = ["한국의약품안전관리원_병용금기약물_20260731.csv"] + sorted(glob.glob("*.csv"))
    csv_path = next((f for f in target_files if os.path.exists(f)), None)
    if not csv_path:
        return pd.DataFrame(), None, None, 0, "CSV 파일 없음"

    df = None
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            df = pd.read_csv(csv_path, encoding=enc, low_memory=False)
            break
        except Exception:
            continue

    if df is None or df.empty:
        return pd.DataFrame(), csv_path, None, 0, "CSV 읽기 실패"

    cols = list(df.columns)

    def pick_col(candidates, exclude=None):
        for c in cols:
            if exclude and c == exclude:
                continue
            for kw in candidates:
                if kw in c.replace(" ", ""):
                    return c
        return None

    col_a = pick_col(["성분명A", "성분명1", "INGR_KOR_NAME_A", "성분명", "제품명A"])
    col_b = pick_col(["병용금기성분명", "성분명B", "성분명2", "INGR_KOR_NAME_B", "금기성분", "제품명B"], exclude=col_a)
    col_reason = pick_col(["금기사유", "상세정보", "PROHBT_CONTENT", "비고", "사유"])
    if not col_a and len(cols) >= 2:
        col_a, col_b = cols[0], cols[1]
    if not col_reason and len(cols) >= 3:
        col_reason = cols[-1]

    return df, csv_path, (col_a, col_b, col_reason), len(df), None


@st.cache_data(show_spinner=False)
def build_dur_ingredient_vocab(dur_df: pd.DataFrame, dur_cols) -> list:
    if dur_df.empty or not dur_cols:
        return []
    col_a, col_b, _ = dur_cols
    vocab = set()
    for col in (col_a, col_b):
        if not col or col not in dur_df.columns:
            continue
        series = dur_df[col].dropna().astype(str).head(25000)
        for val in series:
            for token in re.split(r"[,/();+]", val):
                t = re.sub(r"[^가-힣a-zA-Z]", "", token).strip()
                if 2 <= len(t) <= 12:
                    vocab.add(t)
    return sorted(vocab, key=len, reverse=True)[:4000]


# ==========================================================
# 4. 식약처 API(e약은요 + 의약품 제품 허가정보08 + 건기식) 검색 엔진
# ==========================================================
def normalize_key(raw_key: str) -> str:
    return unquote(raw_key.strip())


def unwrap_items(raw_items) -> list:
    if not raw_items:
        return []
    if isinstance(raw_items, list):
        out = []
        for elem in raw_items:
            if isinstance(elem, dict) and "item" in elem and len(elem) == 1:
                out.extend(unwrap_items(elem["item"]))
            elif isinstance(elem, dict):
                out.append(elem)
        return out
    if isinstance(raw_items, dict):
        if "item" in raw_items:
            return unwrap_items(raw_items["item"])
        return [raw_items]
    return []


def parse_xml_items(xml_text: str):
    try:
        root = ET.fromstring(xml_text)
        auth_msg = root.findtext(".//returnAuthMsg")
        if auth_msg:
            return [], auth_msg.strip(), None
        err_msg = root.findtext(".//errMsg")
        if err_msg:
            return [], err_msg.strip(), None
        res_code = (root.findtext(".//resultCode") or "00").strip()
        res_msg = (root.findtext(".//resultMsg") or res_code).strip()
        if res_code not in ("00", "0", ""):
            return [], res_msg, None
        item_nodes = root.findall(".//items/item")
        rows = []
        for node in item_nodes:
            d = {}
            for child in node:
                d[child.tag] = (child.text or "").strip()
            if d:
                rows.append(d)
        sample_raw = rows[0] if rows else None
        return rows, f"성공 ({len(rows)}건 · XML)", sample_raw
    except Exception as e:
        return [], f"XML 파싱 오류 ({type(e).__name__})", None


def safe_get_json(url: str, params: dict):
    try:
        res = requests.get(url, params=params, timeout=4.5)
        if res.status_code != 200:
            detail = re.sub(r"\s+", " ", res.text or "").strip()[:120]
            msg = f"HTTP {res.status_code}" + (f" ({detail})" if detail else "")
            return [], msg, None
        text = (res.text or "").strip()
        if not text:
            return [], "빈 응답 본문", None
        if text.startswith("<"):
            return parse_xml_items(text)
        data = res.json()
        header = data.get("header", {})
        res_code = str(header.get("resultCode", "00"))
        if res_code not in ("00", "0", "None", ""):
            return [], str(header.get("resultMsg", res_code)), None
        body = data.get("body", {})
        raw_items = body.get("items", []) if isinstance(body, dict) else []
        items = unwrap_items(raw_items)
        sample_raw = items[0] if items else None
        return items, f"성공 ({len(items)}건)", sample_raw
    except requests.exceptions.Timeout:
        return [], "응답 시간 초과 (4.5초)", None
    except Exception as e:
        return [], f"연결 오류 ({type(e).__name__})", None


def get_ci(item: dict, keys: list, default: str = "") -> str:
    if not isinstance(item, dict):
        return default
    lower_map = {str(k).lower(): v for k, v in item.items()}
    for k in keys:
        val = item.get(k)
        if val is None:
            val = lower_map.get(k.lower())
        if val is not None and not pd.isna(val):
            s = str(val).strip()
            if s and s.upper() != "NULL":
                return s
    return default


def query_eyakeunyo(api_key: str, item_name: str, num_rows: int = 20):
    url = "https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
    params = {"serviceKey": normalize_key(api_key), "itemName": item_name, "type": "json", "numOfRows": num_rows, "pageNo": 1}
    return safe_get_json(url, params)


def query_drug_prmsn(api_key: str, item_name: str, num_rows: int = 20):
    operations = [
        "getDrugPrdtPrmsnInq08",
        "getDrugPrdtPrmsnDtlInq08",
    ]
    base_url = "https://apis.data.go.kr/1471000/DrugPrdtPrmsnInfoService08"
    last_st = "미조회"
    last_sample = None

    for op in operations:
        url = f"{base_url}/{op}"
        for req_type in ("json", "xml"):
            params = {
                "serviceKey": normalize_key(api_key),
                "item_name": item_name,
                "type": req_type,
                "numOfRows": str(num_rows),
                "pageNo": "1",
            }
            items, st_msg, sample = safe_get_json(url, params)
            last_st = f"{op}({req_type}) -> {st_msg}"
            if sample:
                last_sample = sample
            if items:
                return items, last_st, sample
    return [], last_st, last_sample


def query_health_food(api_key: str, prduct_name: str, num_rows: int = 20):
    endpoints = [
        "https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsItem01",
        "https://apis.data.go.kr/1471000/HtfsInfoService02/getHtfsItem01",
    ]
    last_st = "미조회"
    last_sample = None
    for url in endpoints:
        for pk in ("Prduct", "PRDUCT"):
            params = {"serviceKey": normalize_key(api_key), pk: prduct_name, "type": "json", "numOfRows": num_rows, "pageNo": 1}
            items, st_msg, sample = safe_get_json(url, params)
            last_st = st_msg
            if sample:
                last_sample = sample
            if items:
                return items, st_msg, sample
    return [], last_st, last_sample


def clean_html(text, max_len: int = 350) -> str:
    if not text or pd.isna(text):
        return ""
    s = str(text)
    if s.strip().upper() == "NULL":
        return ""
    s = re.sub(r"<!\[CDATA\[|\]\]>", " ", s)
    s = re.sub(r"\\n|\r|\n", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip().replace("~", "-")
    return s[:max_len] if s else ""


COMMON_INGREDIENTS = [
    "시메티콘", "우르소데옥시콜산", "판크레아틴", "디아스타제", "프로테아제", "셀룰라제",
    "메틸메티오닌설포늄클로라이드", "탄산수소나트륨", "인산알루미늄", "수산화마그네슘",
    "알긴산나트륨", "탄산칼슘", "파모티딘", "오메프라졸", "에소메프라졸", "라베프라졸", "레바미피드",
    "아세트아미노펜", "이부프로펜", "덱시부프로펜", "나프록센", "록소프로펜", "아세클로페낙", "세레콕시브",
    "아스피린", "무수카페인", "이소프로필안티피린", "파마브롬",
    "클로르페니라민", "세티리진", "로라타딘", "펙소페나딘", "슈도에페드린", "구아이페네신",
    "덱스트로메토르판", "트라마돌", "덱스판테놀", "판테놀",
    "메트포르민", "글리메피리드", "시타글립틴", "아토르바스타틴", "로수바스타틴",
    "암로디핀", "텔미사르탄", "로사르탄", "와파린", "클로피도그렐",
    "에스시탈로프람", "설트랄린", "아목시실린", "클래리트로마이신", "시프로플록사신",
    "레보플록사신", "독시사이클린", "알렌드로네이트", "레보티록신",
    "홍삼", "인삼", "진세노사이드", "프로바이오틱스", "유산균", "오메가3", "마그네슘",
    "밀크씨슬", "실리마린", "루테인", "지아잔틴", "비타민B", "비타민C", "비타민D", "아연",
]

EN_TO_KO_INGREDIENTS = {
    "loxoprofen": "록소프로펜",
    "acetaminophen": "아세트아미노펜",
    "ibuprofen": "이부프로펜",
    "dexibuprofen": "덱시부프로펜",
    "naproxen": "나프록센",
    "aceclofenac": "아세클로페낙",
    "celecoxib": "세레콕시브",
    "aspirin": "아스피린",
    "omeprazole": "오메프라졸",
    "esomeprazole": "에소메프라졸",
    "rebamipide": "레바미피드",
    "amoxicillin": "아목시실린",
    "clarithromycin": "클래리트로마이신",
    "metformin": "메트포르민",
    "atorvastatin": "아토르바스타틴",
    "rosuvastatin": "로수바스타틴",
    "amlodipine": "암로디핀",
    "telmisartan": "텔미사르탄",
    "losartan": "로사르탄",
    "warfarin": "와파린",
    "clopidogrel": "클로피도그렐",
    "cetirizine": "세티리진",
}

TEXT_TO_INGREDIENT_HINTS = {
    "위장관 내 가스": "시메티콘",
    "가스 제거": "시메티콘",
    "담즙": "우르소데옥시콜산",
    "소화효소": "판크레아틴",
    "간손상": "아세트아미노펜",
    "간독성": "아세트아미노펜",
    "위장관 출혈": "이부프로펜",
    "졸음": "클로르페니라민",
    "혈중 중성지질": "오메가3",
    "혈행 개선": "오메가3",
    "유산균 증식": "프로바이오틱스",
    "신경 및 근육 기능": "마그네슘",
    "간 건강": "밀크씨슬",
    "황반색소밀도": "루테인",
}


def suggest_from_dur_csv(query: str, dur_df: pd.DataFrame, dur_cols) -> list:
    if dur_df.empty or not dur_cols or len(query.strip()) < 2:
        return []
    col_a, col_b, _ = dur_cols
    q_stem = re.sub(r"(연질캡슐|경질캡슐|장용정|서방정|캡슐|정|액|시럽)$", "", query.strip())
    if len(q_stem) < 2:
        q_stem = query.strip()

    hits = []
    for col in (col_a, col_b):
        if not col or col not in dur_df.columns:
            continue
        matched = dur_df[dur_df[col].astype(str).str.contains(re.escape(q_stem), na=False)][col].dropna().astype(str).head(15)
        for val in matched:
            for token in re.split(r"[,/();+]", val):
                t = token.strip()
                if 2 <= len(t) <= 20 and t not in hits:
                    hits.append(t)
                if len(hits) >= 5:
                    return hits
    return hits[:5]


def extract_ingredients_from_text(combined_text: str, dur_vocab: list) -> list:
    found = []

    def add_ing(name: str):
        n = name.strip()
        if len(n) >= 2 and n not in found:
            found.append(n)

    if combined_text:
        low_txt = combined_text.lower()
        for en_key, ko_val in EN_TO_KO_INGREDIENTS.items():
            if en_key in low_txt:
                add_ing(ko_val)

        for kw in COMMON_INGREDIENTS:
            if kw in combined_text:
                add_ing(kw)

        for hint_phrase, ing_name in TEXT_TO_INGREDIENT_HINTS.items():
            if hint_phrase in combined_text:
                add_ing(ing_name)

        for v in dur_vocab:
            if len(v) >= 3 and v in combined_text:
                add_ing(v)
            if len(found) >= 6:
                break

    return found[:6]


def build_query_variants(query: str) -> list:
    q = re.sub(r"\s+", "", query).strip()
    variants = [q]
    stripped = re.sub(
        r"(연질캡슐|경질캡슐|장용정|서방정|츄어블정|내복액|현탁액|건조시럽|더블정|플러스정|캡슐|정|액|산|과립|시럽)$",
        "",
        q,
    )
    if len(stripped) >= 2 and stripped not in variants:
        variants.append(stripped)
    if len(stripped) >= 4:
        stem = stripped[:4]
        if stem not in variants:
            variants.append(stem)
    return variants[:3]


def infer_slot_from_text(dosage_text: str, category: str) -> str:
    if category == "일반의약품":
        return "필요시 복용"
    txt = str(dosage_text)
    if "취침" in txt or "자기 전" in txt:
        return "취침 전"
    if "공복" in txt or "기상" in txt:
        return "기상 직후 (공복)"

    timing = "식후 30분"
    if "식후 직후" in txt or "식사 직후" in txt or "식사 바로" in txt or "식후 바로" in txt:
        timing = "식후 직후"
    elif "식전" in txt or "식사 전" in txt:
        timing = "식전"

    if "3회" in txt or ("아침" in txt and "점심" in txt and "저녁" in txt):
        return f"아침·점심·저녁 {timing}"
    if "2회" in txt or ("아침" in txt and "저녁" in txt):
        return f"아침·저녁 {timing}"
    if "저녁" in txt:
        return f"저녁 {timing}"
    if "점심" in txt:
        return f"점심 {timing}"
    return f"아침 {timing}"


def build_record_from_drug_item(item: dict, dur_vocab: list, source_label: str) -> dict:
    name = get_ci(item, ["itemName", "ITEM_NAME", "item_name", "itemNm", "ITEM_NM", "PRDUCT_NM", "prductNm"])
    company = get_ci(item, ["entpName", "ENTP_NAME", "entp_name", "entpNm", "ENTP_NM"])
    spclty = get_ci(item, ["SPCLTY_PBLC", "spclty_pblc", "ETC_OTC_CODE", "etc_otc_code", "etcOtcCode"])
    prduct_type = clean_html(get_ci(item, ["PRDUCT_TYPE", "prduct_type", "CLASS_NAME", "class_name", "className"]))
    material_raw = clean_html(get_ci(item, ["ITEM_INGR_NAME", "item_ingr_name", "MATERIAL_NAME", "material_name", "MAIN_INGR", "main_ingr"]))
    permit_date = get_ci(item, ["ITEM_PERMIT_DATE", "item_permit_date"])

    efficacy = clean_html(get_ci(item, ["efcyQesitm", "EFCY_QESITM", "EFCY"])) or prduct_type
    dosage = clean_html(get_ci(item, ["useMethodQesitm", "USE_METHOD_QESITM", "USE_METHOD"]))
    precautions = clean_html(get_ci(item, ["atpnQesitm", "ATPN_QESITM", "ATPN"]))

    if "전문의약품" in spclty:
        category = "전문의약품"
    elif "일반의약품" in spclty:
        category = "일반의약품"
    elif "전문의약품" in precautions:
        category = "전문의약품"
    else:
        category = "일반의약품"

    combined = f"{name} {material_raw} {efficacy} {dosage} {precautions} {spclty} {prduct_type}"
    ingredients = extract_ingredients_from_text(combined, dur_vocab)
    if not ingredients and material_raw:
        for tok in re.split(r"[,/();+]", material_raw):
            t = tok.strip()
            if 2 <= len(t) <= 30 and t not in ingredients:
                ingredients.append(t)
            if len(ingredients) >= 4:
                break

    if not dosage:
        if category == "전문의약품":
            dosage = "의사 처방 용법·용량에 따라 복용 (식후 30분·식후 직후·식전 등 처방 기준 준수)"
        else:
            dosage = "증상 발현 시(필요시) 제품 설명서 및 약사 안내에 따라 복용 (중복 성분·계열 확인)"

    if not precautions:
        ingr_summary = ", ".join(ingredients) if ingredients else (material_raw or "성분 정보 확인 필요")
        type_summary = prduct_type or category
        permit_txt = f" (허가일자 {permit_date})" if permit_date else ""
        precautions = f"[{type_summary}{permit_txt}] 주성분({ingr_summary}) 중복·병용 여부 및 이상반응 확인 필요"

    label = f"{name} ({company})" if company else name
    return {
        "label": label,
        "name": name,
        "category": category,
        "company": company,
        "ingredients": ingredients,
        "efficacy": efficacy,
        "dosage": dosage,
        "precautions": precautions,
        "default_slot": infer_slot_from_text(dosage, category),
        "source": source_label,
        "matched": bool(name),
    }


def build_record_from_hf_item(item: dict, dur_vocab: list, source_label: str) -> dict:
    name = get_ci(
        item,
        [
            "PRDUCT", "prduct", "PRDUCT_NM", "prduct_nm", "prductNm",
            "itemName", "ITEM_NAME", "ITEM_NM", "itemNm", "식품명", "제품명",
        ],
    )
    company = get_ci(
        item,
        ["ENTRPS", "entrps", "ENTRPS_NM", "entrps_nm", "entrpsNm", "entpName", "ENTP_NAME", "업소명"],
    )
    category = "건강기능식품"
    raw_m = get_ci(item, ["RAWMTRL_NM", "rawmtrl_nm", "rawmtrlNm", "BASE_STANDARD", "base_standard"])
    fnctn = clean_html(get_ci(item, ["MAIN_FNCTN", "main_fnctn", "mainFnctn", "FNCTN", "fnctn"]))
    srv_use = clean_html(get_ci(item, ["SRV_USE", "srv_use", "srvUse", "INTAKE_METHOD", "intakeMethod"]))
    hint = clean_html(get_ci(item, ["INTAKE_HINT1", "intake_hint1", "intakeHint1", "ATPN", "atpn"]))
    if not hint:
        hint = clean_html(get_ci(item, ["PRSRV_PD", "prsrv_pd", "prsrvPd"]))

    ingrs = [re.sub(r"\(.*?\)", "", x).strip() for x in re.split(r"[,|/]", raw_m) if len(x.strip()) >= 2]
    if not ingrs:
        combined = f"{name} {fnctn} {hint}"
        ingrs = extract_ingredients_from_text(combined, dur_vocab)
    if not ingrs and ("오메가3" in name.replace(" ", "") or "프로메가" in name.replace(" ", "")):
        ingrs = ["오메가3", "EPA 및 DHA 함유 유지"]

    label = f"{name} ({company})" if company else name
    return {
        "label": label,
        "name": name,
        "category": category,
        "company": company,
        "ingredients": list(dict.fromkeys(ingrs))[:6],
        "efficacy": fnctn,
        "dosage": srv_use or "제품 표시 섭취량 및 섭취방법 준수",
        "precautions": hint or "건강기능식품 섭취 주의사항 및 의약품 병용 여부 확인",
        "default_slot": infer_slot_from_text(srv_use, category),
        "source": source_label,
        "matched": bool(name),
    }


def search_candidates_by_name(api_key: str, query: str, dur_vocab: list, dur_df: pd.DataFrame, dur_cols) -> tuple:
    logs = {}
    q_clean = query.strip()
    candidates = []

    if len(q_clean) < 2:
        return candidates, logs

    q_nospace = re.sub(r"\s+", "", q_clean)
    variants = list(dict.fromkeys([q_nospace] + build_query_variants(q_clean)))[:3]
    hf_queries = list(dict.fromkeys([q_clean, q_nospace] + variants))[:3]

    is_supp_kw = any(
        k in q_nospace
        for k in [
            "오메가3", "오메가-3", "프로메가", "정관장", "아이패스", "홍삼", "인삼",
            "유산균", "프로바이오틱스", "비타민", "마그네슘", "루테인", "밀크씨슬", "아연",
        ]
    )

    if api_key:
        seen_labels = set()
        prmsn_found = False

        # 1. 의약품 제품 허가정보08 조회
        for qv in variants[:2]:
            try:
                pi, st_prmsn, sample_p = query_drug_prmsn(api_key, qv, num_rows=20)
            except Exception as e:
                pi, st_prmsn, sample_p = [], f"예외 발생 ({type(e).__name__})", None
            logs[f"허가정보08({qv})"] = st_prmsn
            if sample_p and f"허가정보08_원본샘플({qv})" not in logs:
                logs[f"허가정보08_원본샘플({qv})"] = sample_p
            for x in pi:
                rec = build_record_from_drug_item(x, dur_vocab, "식약처 공공데이터 API (의약품 제품 허가정보08)")
                if rec["name"] and rec["label"] not in seen_labels:
                    seen_labels.add(rec["label"])
                    candidates.append(rec)
                    prmsn_found = True
            if prmsn_found:
                break

        # 2. e약은요 조회
        for qv in variants:
            try:
                ei, st_easy, sample_e = query_eyakeunyo(api_key, qv, num_rows=20)
            except Exception as e:
                ei, st_easy, sample_e = [], f"예외 발생 ({type(e).__name__})", None
            logs[f"e약은요({qv})"] = st_easy
            if sample_e and f"e약은요_원본샘플({qv})" not in logs:
                logs[f"e약은요_원본샘플({qv})"] = sample_e
            for x in ei:
                rec = build_record_from_drug_item(x, dur_vocab, "식약처 공공데이터 API (e약은요)")
                if rec["name"] and rec["label"] not in seen_labels:
                    seen_labels.add(rec["label"])
                    candidates.append(rec)
            if ei and prmsn_found:
                break

        # 3. 의약품 결과 유무와 관계없이 건강기능식품 API도 함께 조회 (띄어쓰기 포함/제거 변형 시도)
        for qv in hf_queries:
            try:
                hi, st_hf, sample_h = query_health_food(api_key, qv, num_rows=20)
            except Exception as e:
                hi, st_hf, sample_h = [], f"예외 발생 ({type(e).__name__})", None
            logs[f"건강기능식품({qv})"] = st_hf
            if sample_h and f"건기식_원본샘플({qv})" not in logs:
                logs[f"건기식_원본샘플({qv})"] = sample_h
            for x in hi:
                rec = build_record_from_hf_item(x, dur_vocab, "식약처 공공데이터 API (건강기능식품)")
                if rec["name"] and rec["label"] not in seen_labels:
                    seen_labels.add(rec["label"])
                    candidates.append(rec)
            if hi:
                break

    q_compact = q_nospace.lower()
    if candidates and q_compact:
        candidates.sort(
            key=lambda c: (
                0 if re.sub(r"\s+", "", c["name"]).lower().startswith(q_compact) else (
                    1 if q_compact in re.sub(r"\s+", "", c["name"]).lower() else 2
                )
            )
        )

    if not candidates:
        default_ingrs = extract_ingredients_from_text(q_clean, dur_vocab)
        if not default_ingrs:
            default_ingrs = suggest_from_dur_csv(q_clean, dur_df, dur_cols)
        if is_supp_kw and not default_ingrs:
            default_ingrs = [q_clean]

        source_note = (
            "로컬 DUR CSV 성분 매칭 보조 (API 미조회 품목)"
            if default_ingrs
            else "식약처 API 조회 결과 없음 · 아래에서 성분·구분을 선택/입력하세요"
        )
        candidates.append({
            "label": q_clean,
            "name": q_clean,
            "category": "건강기능식품" if is_supp_kw else "일반의약품",
            "company": "",
            "ingredients": default_ingrs,
            "efficacy": "",
            "dosage": "",
            "precautions": "",
            "default_slot": "아침" if is_supp_kw else "필요시 복용",
            "source": source_note,
            "matched": False,
        })

    return candidates, logs


# ==========================================================
# 5. 식약처 DUR + 건강기능식품 종합정보서비스 병용 분석 엔진
# ==========================================================
NSAID_TOKENS = {"이부프로펜", "나프록센", "덱시부프로펜", "록소프로펜", "아세클로페낙", "세레콕시브", "아스피린"}

CLINICAL_DRUG_RULES = [
    (
        {"아세트아미노펜"},
        {"아세트아미노펜"},
        "동일 성분(아세트아미노펜) 중복 복용 시 간독성 위험이 있습니다. 1일 최대 허용량을 초과하지 않도록 주의하고, 중복 복용을 피하거나 간격·총량을 약사·의사와 확인하세요.",
    ),
    (
        NSAID_TOKENS,
        NSAID_TOKENS,
        "NSAIDs 계열 소염진통제 중복으로 위장관 출혈 위험이 증가합니다. 동일 계열 중복 복용을 피하고 복용 간격·용량을 약사·의사와 확인하세요.",
    ),
    (
        {"와파린"},
        {"아스피린", "이부프로펜", "클로피도그렐"},
        "항응고·항혈소판 작용 중복으로 출혈 위험이 높아집니다.",
    ),
]

MFDS_SUPP_DRUG_DB = [
    {
        "supp_keywords": ["인삼", "홍삼", "진세노사이드"],
        "supp_label": "인삼·홍삼",
        "drug_keywords": ["와파린", "아스피린", "클로피도그렐", "메트포르민", "글리메피리드", "시타글립틴", "인슐린"],
        "drug_class_label": "혈액항응고제·항혈소판제·당뇨병 치료제",
        "reason": "진세노사이드 성분이 혈소판 응집 억제 및 혈당 변화에 영향을 주어 약효 변동이나 출혈 위험이 커질 수 있습니다.",
        "source": "식약처 건강기능식품 종합정보서비스 (의약품 병용 섭취정보)",
    },
    {
        "supp_keywords": ["프로바이오틱스", "유산균"],
        "supp_label": "프로바이오틱스(유산균)",
        "drug_keywords": ["아목시실린", "클래리트로마이신", "시프로플록사신", "레보플록사신", "독시사이클린", "항생제"],
        "drug_class_label": "항생제",
        "reason": "항생제와 동시 복용 시 유익균이 사멸할 수 있으므로 최소 2시간 이상 간격을 두고 분리 섭취해야 합니다.",
        "source": "식약처 건강기능식품 종합정보서비스 (의약품 병용 섭취정보)",
    },
    {
        "supp_keywords": ["오메가3", "epa", "dha"],
        "supp_label": "EPA 및 DHA 함유 유지(오메가3)",
        "drug_keywords": ["와파린", "아스피린", "클로피도그렐", "이부프로펜", "나프록센", "덱시부프로펜", "록소프로펜", "암로디핀", "로사르탄", "텔미사르탄"],
        "drug_class_label": "항응고제·소염진통제·혈압강하제",
        "reason": "혈소판 응집 억제 및 혈압 강하 작용이 중첩되어 출혈 경향이나 저혈압 위험이 증가할 수 있습니다.",
        "source": "식약처 건강기능식품 종합정보서비스 (의약품 병용 섭취정보)",
    },
    {
        "supp_keywords": ["마그네슘", "칼슘", "철분", "아연"],
        "supp_label": "미네랄(마그네슘·칼슘·철분·아연)",
        "drug_keywords": ["시프로플록사신", "레보플록사신", "독시사이클린", "알렌드로네이트", "레보티록신", "이부프로펜", "아세트아미노펜"],
        "drug_class_label": "항생제·골다공증약·갑상선약·진통제",
        "reason": "2가 양이온 미네랄이 위장관에서 의약품과 결합해 약물 흡수율을 떨어뜨리므로 2시간 이상 간격 분리가 권장됩니다.",
        "source": "식약처 건강기능식품 종합정보서비스 (의약품 병용 섭취정보)",
    },
    {
        "supp_keywords": ["밀크씨슬", "실리마린"],
        "supp_label": "밀크씨슬 추출물(실리마린)",
        "drug_keywords": ["아토르바스타틴", "로수바스타틴", "와파린", "메트포르민", "로사르탄"],
        "drug_class_label": "고지혈증약(스타틴)·항응고제·당뇨약",
        "reason": "간 대사 효소(CYP450) 활성에 영향을 주어 의약품 혈중 농도가 변할 수 있으므로 시간 간격을 두고 복용합니다.",
        "source": "식약처 건강기능식품 종합정보서비스 (의약품 병용 섭취정보)",
    },
]


def analyze_all_interactions(med_list: list, dur_df: pd.DataFrame, dur_cols):
    dur_warnings = []
    supp_warnings = []
    shifted_supp_names = set()
    missing_ingr_meds = [m["name"] for m in med_list if not m.get("ingredients")]

    if len(med_list) < 2:
        return dur_warnings, supp_warnings, shifted_supp_names, missing_ingr_meds

    ingr_owners = {}
    for m in med_list:
        for ingr in m.get("ingredients", []):
            k = re.sub(r"\s+", "", ingr)
            if len(k) >= 2:
                ingr_owners.setdefault(k, []).append(f"{m['name']}({m['category']})")
    for ingr, owners in ingr_owners.items():
        uniq = list(dict.fromkeys(owners))
        if len(uniq) >= 2:
            dur_warnings.append({
                "title": f"동일성분 중복 경고 ({uniq[0]} ↔ {uniq[1]})",
                "desc": f"두 제품 모두 [{ingr}] 성분을 포함합니다. 동일 성분 중복 복용 시 부작용·과량 위험이 있으므로 병용을 피하거나 복용 간격·1일 총량을 약사·의사와 확인하세요.",
            })

    col_a, col_b, col_reason = dur_cols if dur_cols else (None, None, None)
    has_csv = not dur_df.empty and col_a and col_b

    for i in range(len(med_list)):
        for j in range(i + 1, len(med_list)):
            m1, m2 = med_list[i], med_list[j]
            if m1["category"] == "건강기능식품" or m2["category"] == "건강기능식품":
                continue

            t1 = set(m1.get("ingredients", []))
            t2 = set(m2.get("ingredients", []))
            if not t1 or not t2:
                continue

            matched_csv = False
            if has_csv:
                sa = dur_df[col_a].astype(str)
                sb = dur_df[col_b].astype(str)
                for a in t1:
                    if len(a) < 2:
                        continue
                    for b in t2:
                        if len(b) < 2 or a == b:
                            continue
                        cond = (sa.str.contains(re.escape(a), na=False) & sb.str.contains(re.escape(b), na=False)) | (
                            sa.str.contains(re.escape(b), na=False) & sb.str.contains(re.escape(a), na=False)
                        )
                        hits = dur_df[cond]
                        if not hits.empty:
                            reason = str(hits.iloc[0][col_reason]) if col_reason else "식약처 DUR 병용금기 성분 조합"
                            dur_warnings.append({
                                "title": f"DUR 병용금기 ({m1['name']} + {m2['name']})",
                                "desc": f"[{a} + {b}] {reason}",
                            })
                            matched_csv = True
                            break
                    if matched_csv:
                        break

            if not matched_csv:
                for s1, s2, reason in CLINICAL_DRUG_RULES:
                    if (any(any(x in tok for tok in t1) for x in s1) and any(any(y in tok for tok in t2) for y in s2)) or (
                        any(any(y in tok for tok in t1) for y in s2) and any(any(x in tok for tok in t2) for x in s1)
                    ):
                        dur_warnings.append({
                            "title": f"의약품 병용 주의 ({m1['name']} + {m2['name']})",
                            "desc": reason,
                        })
                        break

    supps = [m for m in med_list if m["category"] == "건강기능식품"]
    drugs = [m for m in med_list if m["category"] != "건강기능식품"]

    for sp in supps:
        sp_tokens = " ".join(sp.get("ingredients", []) + [sp["name"]]).lower()
        for dg in drugs:
            dg_tokens = " ".join(dg.get("ingredients", []) + [dg["name"]]).lower()
            for rule in MFDS_SUPP_DRUG_DB:
                if any(sk in sp_tokens for sk in rule["supp_keywords"]) and any(dk in dg_tokens for dk in rule["drug_keywords"]):
                    shifted_supp_names.add(sp["name"])
                    supp_warnings.append({
                        "title": f"{sp['name']} ↔ {dg['name']} ({rule['drug_class_label']})",
                        "reason": rule["reason"],
                        "source": rule["source"],
                    })
                    break

    return dur_warnings, supp_warnings, shifted_supp_names, missing_ingr_meds


def extract_interval_hint_from_med(med: dict) -> str:
    combined = f"{med.get('dosage', '')} {med.get('precautions', '')}"
    if not combined.strip():
        return ""
    sentences = re.split(r"(?<=[.!?다요])\s+", combined)
    matched = []
    for s in sentences:
        if any(k in s for k in ["시간", "간격", "최대", "1일", "회 복용", "복용 간격"]):
            s_clean = s.strip()
            if 5 <= len(s_clean) <= 140 and s_clean not in matched:
                matched.append(s_clean)
        if len(matched) >= 2:
            break
    return " / ".join(matched)


def add_minutes(t: time, mins: int) -> str:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=mins)
    return dt.strftime("%H:%M")


def parse_rx_slot_detail(slot_str: str, t_bf: time, t_lu: time, t_dn: time, t_wake: time, t_sleep: time):
    s = str(slot_str)
    if "기상 직후" in s or "공복" in s:
        return [("기상 직후 (공복)", add_minutes(t_wake, 0), "공복")]
    if "취침 전" in s:
        return [("취침 전", add_minutes(t_sleep, -30), "취침 30분 전")]

    if "식후 직후" in s:
        offset, tag = 5, "식후 직후"
    elif "식전" in s:
        offset, tag = -30, "식전 30분"
    else:
        offset, tag = 30, "식후 30분"

    meals = []
    if "아침" in s:
        meals.append(("아침", add_minutes(t_bf, offset), tag))
    if "점심" in s:
        meals.append(("점심", add_minutes(t_lu, offset), tag))
    if "저녁" in s:
        meals.append(("저녁", add_minutes(t_dn, offset), tag))

    return meals if meals else [("아침", add_minutes(t_bf, offset), tag)]


def generate_ai_schedule(
    selected_meds: list,
    shifted_supp_names: set,
    t_wake: time,
    t_bf: time,
    skip_bf: bool,
    t_lu: time,
    skip_lu: bool,
    t_dn: time,
    skip_dn: bool,
    t_sleep: time,
):
    rx_meds = [m for m in selected_meds if m["category"] == "전문의약품"]
    otc_meds = [m for m in selected_meds if m["category"] == "일반의약품"]
    supp_meds = [m for m in selected_meds if m["category"] == "건강기능식품"]

    ai_decisions = []

    slots = {
        "기상 직후 (공복)": {"icon": "🌅", "time": add_minutes(t_wake, 0), "items": [], "skipped": False},
        "아침": {"icon": "☀️", "time": add_minutes(t_bf, 30), "items": [], "skipped": skip_bf},
        "점심": {"icon": "⛅", "time": add_minutes(t_lu, 30), "items": [], "skipped": skip_lu},
        "저녁": {"icon": "🌙", "time": add_minutes(t_dn, 30), "items": [], "skipped": skip_dn},
        "취침 전": {"icon": "🛌", "time": add_minutes(t_sleep, -30), "items": [], "skipped": False},
    }

    rx_occupied_slots = set()
    drug_occupied_slots = set()

    for m in rx_meds:
        s = m.get("slot", "아침 식후 30분")
        ingr_lbl = f" ({', '.join(m['ingredients'][:2])})" if m.get("ingredients") else " (성분 미입력)"
        parsed_targets = parse_rx_slot_detail(s, t_bf, t_lu, t_dn, t_wake, t_sleep)

        for k, exact_t, tag in parsed_targets:
            rx_occupied_slots.add(k)
            drug_occupied_slots.add(k)
            slots[k]["items"].append(f"[{exact_t} · {tag}] {m['name']}{ingr_lbl} (전문의약품)")

    if otc_meds:
        for m in otc_meds:
            ingr_lbl = f" ({', '.join(m['ingredients'][:2])})" if m.get("ingredients") else " (성분 미입력)"
            st_str = str(m.get("slot", "")).strip()
            if st_str and st_str != "필요시 복용" and st_str in slots and not slots[st_str]["skipped"]:
                drug_occupied_slots.add(st_str)
                slots[st_str]["items"].append(f"[{slots[st_str]['time']} · 필요시] {m['name']}{ingr_lbl} (일반의약품)")
            else:
                api_hint = extract_interval_hint_from_med(m)
                ingr_join = " ".join(m.get("ingredients", []) + [m["name"]])

                if "아세트아미노펜" in ingr_join or "타이레놀" in ingr_join:
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 아세트아미노펜 계열은 일반적으로 "
                        "<b>약 4~6시간 간격</b> 및 <b>1일 최대 허용량</b> 초과 여부를 확인하는 기준이 참고됩니다."
                    )
                elif any(k in ingr_join for k in ["이부프로펜", "덱시부프로펜", "이지엔"]):
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 이부프로펜·덱시부프로펜 계열은 일반적으로 "
                        "<b>약 4~6시간 간격</b>이 참고되며, 다른 소염진통제(NSAIDs)와 중복 여부 및 위장 부담을 확인하세요."
                    )
                elif any(k in ingr_join for k in ["나프록센", "탁센"]):
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 나프록센 계열은 비교적 작용 시간이 길어 일반적으로 "
                        "<b>약 8~12시간 간격</b>이 참고되며, 다른 소염진통제·진통제와 중복 복용 여부를 확인하세요."
                    )
                elif any(k in ingr_join for k in NSAID_TOKENS) or "록펜" in ingr_join:
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 소염진통제(NSAIDs) 계열은 다른 소염진통제와의 "
                        "<b>중복 복용 여부</b>를 먼저 확인하고, 제품 설명서 기준 간격·용량을 확인하세요."
                    )
                elif any(k in ingr_join for k in ["세티리진", "로라타딘", "펙소페나딘", "클로르페니라민", "항히스타민"]):
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 항히스타민 계열은 성분·제형에 따라 "
                        "<b>1일 1회 또는 약 8~12시간 간격</b> 등 기준이 다를 수 있으며, 졸음 부작용과 종합감기약 중복을 확인하세요."
                    )
                elif any(k in ingr_join for k in ["시메티콘", "알긴산", "파모티딘", "탄산칼슘", "제산", "위장"]):
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 제산·위장 증상 완화제는 다른 약물과 "
                        "<b>흡수 간섭</b>이 생길 수 있으므로 복용 간격과 제품 설명서 기준을 확인하세요."
                    )
                else:
                    base_guide = (
                        "증상 발현 시(필요시) 복용하는 약이에요. 다른 의약품·영양제와의 "
                        "<b>성분·계열 중복 여부</b>와 제품 설명서의 복용 간격을 확인하세요."
                    )

                if api_hint:
                    ai_decisions.append(
                        f"💊 <b>일반의약품(필요시 복용) 안내 — {m['name']}{ingr_lbl}:</b> "
                        f"{base_guide} (API 기재 기준: <b>{api_hint}</b>)"
                    )
                else:
                    ai_decisions.append(
                        f"💊 <b>일반의약품(필요시 복용) 안내 — {m['name']}{ingr_lbl}:</b> {base_guide}"
                    )

    candidate_order = ["아침", "점심", "저녁", "취침 전", "기상 직후 (공복)"]
    safe_slots = [k for k in candidate_order if k not in drug_occupied_slots and not slots[k]["skipped"]]

    for m in supp_meds:
        orig_slot = m.get("slot", "아침")
        if orig_slot not in slots:
            orig_slot = "아침"
        ingr_lbl = f" ({', '.join(m['ingredients'][:2])})" if m.get("ingredients") else ""
        needs_shift = (orig_slot in rx_occupied_slots) or (m["name"] in shifted_supp_names and orig_slot in drug_occupied_slots)

        if needs_shift:
            if safe_slots:
                new_slot = safe_slots[0]
                slots[new_slot]["items"].append(
                    f"[{slots[new_slot]['time']}] {m['name']}{ingr_lbl} 🔄 AI 추천 시간 변경 (기존: {orig_slot})"
                )
                ai_decisions.append(
                    f"🔄 <b>건강기능식품 시간대 자동 변경 ({m['name']}):</b> "
                    f"기존 설정된 <b>{orig_slot}</b> 시간대에 의약품이 배정되어 흡수 간섭·병용 주의를 피하기 위해 "
                    f"의약품과 겹치지 않는 <b>{new_slot}({slots[new_slot]['time']})</b>으로 AI가 자동 변경했어요."
                )
            else:
                fallback_slot = "취침 전" if "취침 전" not in drug_occupied_slots else "기상 직후 (공복)"
                slots[fallback_slot]["items"].append(
                    f"[{slots[fallback_slot]['time']} · +2시간 분리] {m['name']}{ingr_lbl} 🔄 AI 시간 분리 (기존: {orig_slot})"
                )
                ai_decisions.append(
                    f"🔄 <b>건강기능식품 2시간 간격 분리 ({m['name']}):</b> "
                    f"의약품 복용 시간대와 겹치지 않도록 <b>{fallback_slot}({slots[fallback_slot]['time']})</b>으로 이동해 2시간 이상 복용 간격을 확보했어요."
                )
        else:
            target_s = orig_slot if not slots[orig_slot]["skipped"] else (safe_slots[0] if safe_slots else "취침 전")
            sep_tag = " ⏱️[의약품과 2시간 이상 간격 유지]" if m["name"] in shifted_supp_names else ""
            slots[target_s]["items"].append(f"[{slots[target_s]['time']}] {m['name']}{ingr_lbl} (건강기능식품){sep_tag}")

    return slots, ai_decisions


# ==========================================================
# 6. 세션 상태 초기화 & 사이드바
# ==========================================================
if "my_meds" not in st.session_state:
    st.session_state.my_meds = []
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "💊 내 약통"

dur_df, csv_path, dur_cols, dur_count, csv_err = load_dur_csv()
dur_vocab = build_dur_ingredient_vocab(dur_df, dur_cols)
configured_key = get_configured_api_key()

with st.sidebar:
    st.subheader("⚙️ API 및 데이터 설정")
    active_key = get_configured_api_key()
    if active_key:
        st.success("식약처 API 연결 준비 완료")
    else:
        st.warning("Streamlit Secrets(PUBLIC_DATA_KEY)가 설정되지 않았습니다.")

    if csv_path and not csv_err:
        st.caption(f"DUR DB: {dur_count:,}개 조합 로드됨")

# ==========================================================
# 7. 상단 3단 네비게이션 (내 약통 | 약 등록 | 복용 시간표)
# ==========================================================
nav_options = ["💊 내 약통", "➕ 약 등록", "📅 복용 시간표"]
selected_nav = st.radio(
    "메뉴 이동",
    nav_options,
    index=nav_options.index(st.session_state.nav_page),
    horizontal=True,
    label_visibility="collapsed",
)
if selected_nav != st.session_state.nav_page:
    st.session_state.nav_page = selected_nav
    st.rerun()

today = date.today()

# ==========================================================
# PAGE 1: 내 약통
# ==========================================================
if st.session_state.nav_page == "💊 내 약통":
    st.markdown('<div class="yagiyagi-brand">야기야기</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="yagiyagi-title">내 약통</h1>', unsafe_allow_html=True)

    total_cnt = len(st.session_state.my_meds)
    expiring_cnt = sum(1 for m in st.session_state.my_meds if (m["expiry"] - today).days <= 30)

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-grid">
                <div class="hero-col">
                    <div class="hero-label">📦 등록된 약·영양제</div>
                    <div class="hero-num">{total_cnt}<span>개</span></div>
                </div>
                <div class="hero-divider"></div>
                <div class="hero-col">
                    <div class="hero-label">⚠️ 유통기한 임박</div>
                    <div class="hero-num">{expiring_cnt}<span>개</span></div>
                </div>
            </div>
            <div class="hero-sub">30일 이내 만료 또는 이미 만료된 제품 기준</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if total_cnt == 0:
        st.markdown(
            """
            <div class="empty-card">
                <div style="font-size: 2.6rem; color: #56A597; margin-bottom: 0.6rem;">📦</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #111827; margin-bottom: 0.35rem;">
                    아직 등록된 약이 없어요
                </div>
                <div style="font-size: 0.9rem; color: #6B7280;">
                    약·영양제 이름을 검색해 성분과 복용 시간표를 관리해 보세요.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_sp1, col_btn, col_sp2 = st.columns([1, 2, 1])
        if col_btn.button("＋ 첫 약 등록하기", type="primary", use_container_width=True):
            st.session_state.nav_page = "➕ 약 등록"
            st.rerun()
    else:
        for idx, med in enumerate(st.session_state.my_meds):
            dday = (med["expiry"] - today).days
            if dday < 0:
                badge_html = f'<span class="badge-danger">만료됨 (D+{abs(dday)})</span>'
            elif dday <= 30:
                badge_html = f'<span class="badge-warn">만료 임박 (D-{dday})</span>'
            else:
                badge_html = f'<span class="badge-mint">정상 (D-{dday})</span>'

            ingr_txt = ", ".join(med["ingredients"]) if med.get("ingredients") else "미입력 (DUR 검사 제한)"
            slot_display = "아플 때 / 필요시 복용 (중복·간격 기준 안내)" if med["category"] == "일반의약품" else med["slot"]
            exp_label = "처방·조제 복용 기준일" if med["category"] == "전문의약품" else "유통기한"
            with st.container():
                c_card, c_del = st.columns([5, 1])
                with c_card:
                    st.markdown(
                        f"""
                        <div class="med-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                                <span style="font-weight:800; font-size:1.05rem; color:#111827;">{med['name']}</span>
                                {badge_html}
                            </div>
                            <div style="font-size:0.83rem; color:#4B5563; margin-bottom:4px;">
                                <b>구분:</b> {med['category']} · <b>주성분:</b> {ingr_txt}
                            </div>
                            <div style="font-size:0.82rem; color:#6B7280;">
                                <b>{exp_label}:</b> {med['expiry']} · <b>복용 기준:</b> {slot_display}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c_del:
                    st.write("")
                    if st.button("삭제", key=f"del_box_{idx}", use_container_width=True):
                        st.session_state.my_meds.pop(idx)
                        st.rerun()

# ==========================================================
# PAGE 2: 약 등록 (제품명 검색 + 복수 후보 선택 + 구분 선택)
# ==========================================================
elif st.session_state.nav_page == "➕ 약 등록":
    st.markdown('<div class="yagiyagi-brand">야기야기</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="yagiyagi-title">약 등록</h1>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="mint-guide-box">
            복용 중인 <b>약 또는 영양제 제품명</b>을 검색하면 관련 제품 목록이 뜨고, 원하는 제품을 선택해 바로 저장할 수 있어요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    m_col1, m_col2 = st.columns([3, 1])
    search_kw = m_col1.text_input(
        "제품명 검색",
        placeholder="예: 타이레놀, 탁센, 록펜정, 프로메가",
        label_visibility="collapsed",
    )
    if m_col2.button("조회", type="primary", use_container_width=True):
        if not search_kw.strip():
            st.warning("조회할 약 또는 영양제 이름을 입력해 주세요.")
        else:
            with st.spinner("식약처 API(e약은요·허가정보08·건기식) 및 DUR 데이터에서 조회 중입니다..."):
                cands, logs = search_candidates_by_name(active_key, search_kw.strip(), dur_vocab, dur_df, dur_cols)
                st.session_state["search_draft"] = {
                    "candidates": cands,
                    "selected_idx": 0,
                    "logs": logs,
                    "expiry": today + timedelta(days=365),
                }

    if "search_draft" in st.session_state:
        sd = st.session_state["search_draft"]
        cands = sd["candidates"]

        st.markdown("---")
        st.subheader("📋 조회 결과 확인 및 약통 저장")

        if len(cands) > 1:
            labels = [c["label"] for c in cands]
            chosen_label = st.selectbox(
                f"검색된 제품 {len(cands)}개 중 선택하세요",
                labels,
                index=min(sd.get("selected_idx", 0), len(labels) - 1),
            )
            chosen_idx = labels.index(chosen_label)
            sd["selected_idx"] = chosen_idx
        else:
            chosen_idx = 0

        info = cands[chosen_idx]
        st.caption(f"데이터 출처: {info['source']}")

        if sd.get("logs"):
            with st.expander("📡 식약처 API 응답 상태 보기"):
                st.json(sd["logs"])

        edit_name = st.text_input("제품명", value=info["name"], key=f"name_{chosen_idx}_{info['name']}")
        c_cat, c_exp = st.columns(2)
        cat_opts = ["일반의약품", "전문의약품", "건강기능식품"]
        cat_idx = cat_opts.index(info["category"]) if info["category"] in cat_opts else 0
        edit_cat = c_cat.selectbox("제품 구분", cat_opts, index=cat_idx, key=f"cat_{chosen_idx}_{info['name']}")

        if edit_cat == "전문의약품":
            exp_title = "유통기한 (처방·조제 일수 기준)"
            default_rx_exp = today + timedelta(days=7)
            exp_val = sd["expiry"] if sd["expiry"] != today + timedelta(days=365) else default_rx_exp
            edit_exp = c_exp.date_input(exp_title, value=exp_val, key=f"exp_rx_{chosen_idx}_{info['name']}")
            st.caption("🏥 전문의약품은 병·의원에서 **처방·조제받은 복용 일수**(예: 3일분, 7일분, 30일분)에 맞춰 날짜를 선택해 주세요.")
        else:
            edit_exp = c_exp.date_input("유통기한 (달력 선택)", value=sd["expiry"], key=f"exp_other_{chosen_idx}_{info['name']}")

        edit_ingr = st.text_input(
            "주성분 / 기능성 원료 (쉼표로 구분)",
            value=", ".join(info["ingredients"]),
            placeholder="예: 록소프로펜, 아세트아미노펜 (입력 시 DUR 중복·병용금기 자동 검사)",
            key=f"ingr_{chosen_idx}_{info['name']}",
        )

        if edit_cat == "일반의약품":
            st.info(
                "💊 **일반의약품**은 증상 발현 시(필요시) 복용하는 약이에요. "
                "중복 성분·계열 여부를 검사하고, API 복용법·주의사항과 성분 계열별 참고 간격을 확인해 안내해요."
            )
            edit_slot = "필요시 복용"
        elif edit_cat == "전문의약품":
            slot_idx = RX_SLOT_OPTIONS.index(info["default_slot"]) if info["default_slot"] in RX_SLOT_OPTIONS else 0
            edit_slot = st.selectbox("처방 복용 시간대 (전문의약품)", RX_SLOT_OPTIONS, index=slot_idx, key=f"slot_rx_{chosen_idx}_{info['name']}")
        else:
            slot_opts = ["아침", "점심", "저녁", "기상 직후 (공복)", "취침 전"]
            slot_idx = slot_opts.index(info["default_slot"]) if info["default_slot"] in slot_opts else 0
            edit_slot = st.selectbox(
                "희망 복용 시간대 (건강기능식품 — 의약품과 겹치면 AI가 자동 변경)",
                slot_opts,
                index=slot_idx,
                key=f"slot_sp_{chosen_idx}_{info['name']}",
            )

        edit_eff = st.text_input("효능·기능성", value=info.get("efficacy", ""), key=f"eff_{chosen_idx}_{info['name']}")
        edit_dos = st.text_input("복용법", value=info.get("dosage", ""), key=f"dos_{chosen_idx}_{info['name']}")
        edit_cau = st.text_input("주의사항", value=info.get("precautions", ""), key=f"cau_{chosen_idx}_{info['name']}")

        if st.button("💾 내 약통에 저장하기", type="primary", use_container_width=True):
            st.session_state.my_meds.append({
                "name": edit_name.strip() or info["name"],
                "category": edit_cat,
                "company": info["company"],
                "ingredients": [x.strip() for x in edit_ingr.split(",") if x.strip()],
                "expiry": edit_exp,
                "efficacy": edit_eff.strip(),
                "dosage": edit_dos.strip(),
                "precautions": edit_cau.strip(),
                "slot": edit_slot,
            })
            del st.session_state["search_draft"]
            st.session_state.nav_page = "💊 내 약통"
            st.rerun()

# ==========================================================
# PAGE 3: 복용 시간표 & 경고
# ==========================================================
elif st.session_state.nav_page == "📅 복용 시간표":
    st.markdown('<div class="yagiyagi-brand">야기야기</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="yagiyagi-title">복용 시간표 & 경고</h1>', unsafe_allow_html=True)

    st.markdown("#### 📅 나의 생활 시간")

    r1_l, r1_r = st.columns([1.2, 2.8])
    r1_l.markdown("<div style='padding-top:8px; font-weight:600;'>기상시간</div>", unsafe_allow_html=True)
    t_wake = r1_r.time_input("기상시간", value=time(7, 0), label_visibility="collapsed")

    r2_l, r2_m, r2_r = st.columns([1.2, 1.8, 1.2])
    r2_l.markdown("<div style='padding-top:8px; font-weight:600;'>아침식사</div>", unsafe_allow_html=True)
    t_bf = r2_m.time_input("아침식사", value=time(8, 0), label_visibility="collapsed")
    skip_bf = r2_r.checkbox("식사 안 함", key="skip_bf")

    r3_l, r3_m, r3_r = st.columns([1.2, 1.8, 1.2])
    r3_l.markdown("<div style='padding-top:8px; font-weight:600;'>점심식사</div>", unsafe_allow_html=True)
    t_lu = r3_m.time_input("점심식사", value=time(12, 30), label_visibility="collapsed")
    skip_lu = r3_r.checkbox("식사 안 함", key="skip_lu")

    r4_l, r4_m, r4_r = st.columns([1.2, 1.8, 1.2])
    r4_l.markdown("<div style='padding-top:8px; font-weight:600;'>저녁식사</div>", unsafe_allow_html=True)
    t_dn = r4_m.time_input("저녁식사", value=time(18, 30), label_visibility="collapsed")
    skip_dn = r4_r.checkbox("식사 안 함", key="skip_dn")

    r5_l, r5_r = st.columns([1.2, 2.8])
    r5_l.markdown("<div style='padding-top:8px; font-weight:600;'>취침시간</div>", unsafe_allow_html=True)
    t_sleep = r5_r.time_input("취침시간", value=time(23, 0), label_visibility="collapsed")

    st.button("📅 맞춤 시간표 생성", type="primary", use_container_width=True)

    st.markdown("---")
    selected_meds = []
    h_left, h_right = st.columns([3, 1])
    h_left.markdown("#### 오늘 복용할 약 선택")

    if not st.session_state.my_meds:
        h_right.markdown("<div style='text-align:right; color:#6B7280; padding-top:6px;'>0개 선택</div>", unsafe_allow_html=True)
        st.caption("등록된 약이 없어요.")
    else:
        for i, m in enumerate(st.session_state.my_meds):
            ingr_hint = f" · {', '.join(m['ingredients'][:2])}" if m.get("ingredients") else " · 성분 미입력"
            if st.checkbox(f"{m['name']} ({m['category']}{ingr_hint})", value=True, key=f"chk_today_{i}"):
                selected_meds.append(m)
        h_right.markdown(
            f"<div style='text-align:right; color:#4EA898; font-weight:700; padding-top:6px;'>{len(selected_meds)}개 선택</div>",
            unsafe_allow_html=True,
        )

    db_cnt_label = f"{dur_count:,}개 조합" if dur_count else "512,464개 조합"
    st.caption(f"DUR 자료 기준일 2026-07-31 · {db_cnt_label} · 식약처 건강기능식품 병용 섭취정보 연동")

    dur_warnings, supp_warnings, shifted_supp_names, missing_ingr_meds = analyze_all_interactions(selected_meds, dur_df, dur_cols)

    if not selected_meds:
        st.caption("오늘 선택한 약이 없어요.")
    else:
        if missing_ingr_meds:
            st.warning(
                f"⚠️ **주성분 미입력 항목 ({', '.join(missing_ingr_meds)})**: "
                f"주성분이 비어 있어 해당 약물의 DUR 병용금기·중복 검사가 제한됩니다. 약 등록에서 주성분을 입력해 주세요."
            )

        if dur_warnings:
            for w in dur_warnings:
                st.error(f"🚨 **{w['title']}**\n\n{w['desc']}")
        else:
            st.success("✅ 주성분이 입력된 의약품 간 DUR 병용금기 및 동일성분 중복이 없습니다.")

        if supp_warnings:
            st.markdown("#### 🌿 건강기능식품 ↔ 의약품 병용 섭취 분석")
            for sw in supp_warnings:
                st.markdown(
                    f"""
                    <div class="supp-warn-card">
                        <b>⚠️ {sw['title']}</b><br/>
                        {sw['reason']}<br/>
                        <span style="font-size:0.78rem; color:#92400E;">출처: {sw['source']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    slots_dict, ai_decisions = generate_ai_schedule(
        selected_meds, shifted_supp_names, t_wake, t_bf, skip_bf, t_lu, skip_lu, t_dn, skip_dn, t_sleep
    )

    if ai_decisions:
        st.markdown("#### 🤖 AI 스마트 복약 간격·시간표 추천")
        for dec in ai_decisions:
            st.markdown(f'<div class="ai-guide-card">{dec}</div>', unsafe_allow_html=True)

    st.markdown("#### 오늘의 복용 타임라인")

    for label in ["기상 직후 (공복)", "아침", "점심", "저녁", "취침 전"]:
        slot = slots_dict[label]
        if slot["skipped"]:
            body_html = '<span style="color:#9CA3AF;">식사 안 함 선택</span>'
        elif slot["items"]:
            body_html = "".join(
                [
                    f'<div style="background:#E7F4F1; color:#1F2937; padding:7px 11px; border-radius:10px; margin-top:5px; font-size:0.85rem; font-weight:600;">💊 {it}</div>'
                    for it in slot["items"]
                ]
            )
        else:
            body_html = '<span style="color:#9CA3AF; font-size:0.88rem;">배정된 제품이 없어요</span>'

        st.markdown(
            f"""
            <div class="timeline-row">
                <div class="timeline-dot">{slot['icon']}</div>
                <div style="width:100%;">
                    <div style="font-size:1.02rem; font-weight:800; color:#111827;">
                        {label} <span style="font-weight:500; color:#6B7280; font-size:0.9rem; margin-left:6px;">{slot['time']}</span>
                    </div>
                    <div style="margin-top:3px;">{body_html}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="disclaimer-box">
            ℹ️ 본 서비스의 분석 결과는 참고용이며, 정확한 복약 지도는 의사·약사와 상담하세요.
        </div>
        """,
        unsafe_allow_html=True,
    )