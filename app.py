import streamlit as st
import hashlib, json, os, io, base64
from datetime import datetime
import qrcode
from PIL import Image

LEDGER_FILE = "ledger.json"

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def ensure_ledger():
    if not os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "w") as f:
            json.dump({"blocks": []}, f, indent=2)

def load_ledger():
    ensure_ledger()
    with open(LEDGER_FILE, "r") as f:
        return json.load(f)

def save_ledger(ledger):
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2)

def last_block_hash(ledger):
    if not ledger["blocks"]:
        return "0" * 64
    return ledger["blocks"][-1]["blockHash"]

def make_block(index, fileHash, prevHash, issuer, filename):
    block = {
        "index": index,
        "timestamp": now_iso(),
        "issuer": issuer,
        "filename": filename,
        "fileHash": fileHash,
        "prevHash": prevHash,
    }
    body_str = json.dumps(block, sort_keys=True)
    block["blockHash"] = hashlib.sha256(body_str.encode()).hexdigest()
    return block

def generate_qr_bytes(text):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

st.set_page_config(page_title="SkillChain", page_icon="🎓", layout="centered")
st.title("🎓 SkillChain — Proof of Learning Network")
st.markdown("Tamper-proof certificates — demo (simulated ledger).")

page = st.sidebar.selectbox("Navigate", ["Home", "Issue Certificate", "Verify Certificate", "View Ledger"])

ensure_ledger()

if page == "Home":
    st.header("What is SkillChain?")
    st.write("SkillChain stores certificate proofs (SHA-256 hashes) in a simple blockchain-like ledger.")
    st.write("Each issued certificate gets a QR that contains a small verification payload (index/blockHash/fileHash).")

elif page == "Issue Certificate":
    st.header("📤 Issue Certificate")
    uploaded = st.file_uploader("Upload certificate (pdf/png/jpg/jpeg)", type=["pdf","png","jpg","jpeg"])
    issuer = st.text_input("Issuer name", "Demo University")

    if uploaded and st.button("Issue"):
        raw = uploaded.read()
        fileHash = sha256_bytes(raw)
        ledger = load_ledger()
        prevHash = last_block_hash(ledger)
        newIndex = len(ledger["blocks"])
        block = make_block(newIndex, fileHash, prevHash, issuer, uploaded.name)
        ledger["blocks"].append(block)
        save_ledger(ledger)

        st.success("✅ Certificate issued and recorded.")
        st.code(block["fileHash"], language="text")
        payload = json.dumps({"index": block["index"], "blockHash": block["blockHash"], "fileHash": block["fileHash"]})
        qr = generate_qr_bytes(payload)
        st.image(qr, caption="Verification QR Code")
        b64 = base64.b64encode(qr).decode()
        st.markdown(f"[Download QR](data:image/png;base64,{b64})", unsafe_allow_html=True)

elif page == "Verify Certificate":
    st.header("🔍 Verify Certificate")
    file = st.file_uploader("Upload to verify", type=["pdf","png","jpg","jpeg"])
    if file and st.button("Verify File"):
        raw = file.read()
        fileHash = sha256_bytes(raw)
        ledger = load_ledger()
        match = [b for b in ledger["blocks"] if b["fileHash"] == fileHash]
        if match:
            st.success("✅ Verified")
            st.json(match[0])
        else:
            st.error("❌ Not found")

elif page == "View Ledger":
    st.header("📚 Ledger")
    ledger = load_ledger()
    for b in ledger["blocks"]:
        with st.expander(f"Block #{b['index']}"):
            st.json(b)
