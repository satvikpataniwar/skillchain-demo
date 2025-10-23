import streamlit as st
import hashlib
import json
import os
import io
import base64
from datetime import datetime
import qrcode
from PIL import Image

# ======================================================
# CONFIG
# ======================================================
LEDGER_FILE = "ledger.json"

# ======================================================
# HELPER FUNCTIONS
# ======================================================
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

def make_block(index, file_hash, prev_hash, issuer, filename):
    block = {
        "index": index,
        "timestamp": now_iso(),
        "issuer": issuer,
        "filename": filename,
        "fileHash": file_hash,
        "prevHash": prev_hash
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

# ======================================================
# STREAMLIT APP
# ======================================================
st.set_page_config(page_title="SkillChain", page_icon="🎓", layout="centered")
st.title("🎓 SkillChain — Proof of Learning Network")
st.markdown("Tamper-proof certificates — blockchain-style verification demo.")

# Sidebar Navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Issue Certificate", "Verify Certificate", "View Ledger"])

# Ensure ledger exists
ensure_ledger()

# ======================================================
# HOME PAGE
# ======================================================
if page == "Home":
    st.header("What is SkillChain?")
    st.write("""
    SkillChain prevents fake certificates by storing their unique digital fingerprints (SHA-256 hashes)
    in a simulated blockchain ledger.  
    Each certificate issued gets a QR code containing its verification data.

    ✅ Employers or HR managers can:
    - Scan the QR code to check authenticity  
    - Or re-upload the same file to confirm it hasn't been tampered with
    """)
    st.info("Think of it as 'UPI for Education & Jobs' — instant, verifiable, and tamper-proof.")

# ======================================================
# ISSUE CERTIFICATE PAGE
# ======================================================
elif page == "Issue Certificate":
    st.header("📤 Issue Certificate")
    uploaded = st.file_uploader("Upload certificate (pdf/png/jpg/jpeg)", type=["pdf", "png", "jpg", "jpeg"])
    issuer = st.text_input("Issuer Name", "Demo University")

    if uploaded and st.button("Issue"):
        raw = uploaded.read()
        file_hash = sha256_bytes(raw)
        ledger = load_ledger()
        prev_hash = last_block_hash(ledger)
        new_index = len(ledger["blocks"])
        block = make_block(new_index, file_hash, prev_hash, issuer, uploaded.name)
        ledger["blocks"].append(block)
        save_ledger(ledger)

        st.success("✅ Certificate issued and recorded successfully.")
        st.write("**File Hash:**")
        st.code(block["fileHash"])
        st.write("**Block Hash:**")
        st.code(block["blockHash"])

        # QR code with verification payload
        payload = json.dumps({
            "index": block["index"],
            "blockHash": block["blockHash"],
            "fileHash": block["fileHash"]
        })
        qr_bytes = generate_qr_bytes(payload)
        st.image(qr_bytes, caption="Scan this QR for verification")

        b64 = base64.b64encode(qr_bytes).decode()
        st.markdown(f"[📥 Download QR](data:image/png;base64,{b64})", unsafe_allow_html=True)

# ======================================================
# VERIFY CERTIFICATE PAGE
# ======================================================
elif page == "Verify Certificate":
    st.header("🔍 Verify Certificate Authenticity")

    uploaded_file = st.file_uploader("Upload certificate to verify", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file and st.button("Verify File"):
        raw = uploaded_file.read()
        file_hash = sha256_bytes(raw)
        ledger = load_ledger()
        match = [b for b in ledger["blocks"] if b["fileHash"] == file_hash]

        if match:
            st.success("✅ Certificate verified — original and untampered.")
            st.json(match[0])
        else:
            st.error("❌ Not found in ledger — may be fake or modified.")

    st.markdown("---")
    st.subheader("Or verify using QR payload or hash")
    qr_text = st.text_area("Paste the QR payload or hash here:")

    if st.button("Verify from QR / Hash") and qr_text.strip():
        ledger = load_ledger()
        verified = False
        try:
            obj = json.loads(qr_text)
            for b in ledger["blocks"]:
                if b["index"] == obj.get("index") and b["blockHash"] == obj.get("blockHash"):
                    st.success("✅ Verified from QR payload.")
                    st.json(b)
                    verified = True
                    break
        except:
            for b in ledger["blocks"]:
                if b["fileHash"] == qr_text.strip() or b["blockHash"] == qr_text.strip():
                    st.success("✅ Verified from hash.")
                    st.json(b)
                    verified = True
                    break

        if not verified:
            st.error("❌ Certificate not verified or not found.")

# ======================================================
# VIEW LEDGER PAGE
# ======================================================
elif page == "View Ledger":
    st.header("📚 Blockchain Ledger")
    ledger = load_ledger()
    if not ledger["blocks"]:
        st.info("No certificates issued yet.")
    else:
        for b in ledger["blocks"]:
            with st.expander(f"Block #{b['index']} — {b['filename']}"):
                st.json(b)

st.markdown("---")
st.caption("Built by TEAM Debuggers • SkillChain Hackathon Project • Fully functional verification demo 🚀")

Final full SkillChain version

