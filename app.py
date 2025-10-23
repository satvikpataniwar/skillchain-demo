# app.py
import streamlit as st
import hashlib, json, os, io, base64
from datetime import datetime
import qrcode
from PIL import Image

# ---------------------------
# Config
# ---------------------------
LEDGER_FILE = "ledger.json"   # default ledger file path
LOGO_FILE = "logo.png"        # optional logo (place in repo)
PAGE_TITLE = "SkillChain — Proof of Learning"
PAGE_ICON = "🎓"

# ---------------------------
# Helpers
# ---------------------------
def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def sha256_bytes(b: bytes):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def ensure_ledger(path=LEDGER_FILE):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({"blocks": []}, f, indent=2)

def load_ledger(path=LEDGER_FILE):
    ensure_ledger(path)
    with open(path, "r") as f:
        return json.load(f)

def save_ledger(ledger, path=LEDGER_FILE):
    with open(path, "w") as f:
        json.dump(ledger, f, indent=2)

def last_block_hash(ledger):
    if not ledger["blocks"]:
        return "0"*64
    return ledger["blocks"][-1]["blockHash"]

def make_block(index, fileHash, prevHash, issuer="Unknown", filename=""):
    body = {
        "index": index,
        "timestamp": now_iso(),
        "issuer": issuer,
        "filename": filename,
        "fileHash": fileHash,
        "prevHash": prevHash
    }
    # deterministic blockHash: hash of sorted JSON body
    body_str = json.dumps(body, sort_keys=True)
    blockHash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()
    body["blockHash"] = blockHash
    return body

def generate_qr_bytes(text):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def download_link_bytes(bytes_data, filename, mime="application/octet-stream"):
    b64 = base64.b64encode(bytes_data).decode()
    return f'data:{mime};base64,{b64}'

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
st.title("🎓 SkillChain — Proof of Learning Network")
st.markdown("**Tamper-proof certificates — demo (simulated ledger).**")

# top - show logo if present
if os.path.exists(LOGO_FILE):
    try:
        logo = Image.open(LOGO_FILE)
        st.image(logo, width=140)
    except Exception:
        pass

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Home", "Issue Certificate", "Verify Certificate", "View Ledger", "Settings"])

# Ensure ledger exists
ensure_ledger()

# Home
if page == "Home":
    st.header("What is SkillChain?")
    st.write("""
    SkillChain stores certificate proofs (SHA-256 hashes) in a simple blockchain-like ledger.
    For the hackathon demo we store ledger entries in a JSON file.  
    Each issued certificate gets a QR that contains a small verification payload (index/blockHash/fileHash).
    """)
    st.markdown("**Quick actions**")
    c1, c2 = st.columns(2)
   if c1.button("Issue Certificate"):
    st.query_params["page"] = "issue"
if c2.button("Verify Certificate"):
    st.query_params["page"] = "verify"

# Issue Certificate
elif page == "Issue Certificate":
    st.header("📤 Issue Certificate")
    st.write("Upload a certificate (PDF or image). The app will create a SHA-256 hash, add a block to the ledger, and create a verification QR code.")
    uploaded = st.file_uploader("Upload certificate (pdf/png/jpg/jpeg)", type=["pdf","png","jpg","jpeg"])
    issuer = st.text_input("Issuer name (example: Demo University)", value="Demo Institution")
    if st.button("Issue") and uploaded:
        raw = uploaded.read()
        fileHash = sha256_bytes(raw)
        ledger = load_ledger()
        prevHash = last_block_hash(ledger)
        newIndex = len(ledger["blocks"])
        block = make_block(newIndex, fileHash, prevHash, issuer=issuer, filename=getattr(uploaded, "name", "uploaded_file"))
        ledger["blocks"].append(block)
        save_ledger(ledger)
        st.success("✅ Certificate issued and recorded in ledger.")
        st.subheader("Certificate Proof")
        st.write("**File Hash (SHA-256):**")
        st.code(block["fileHash"])
        st.write("**Block Hash:**")
        st.code(block["blockHash"])
        st.write("**Block Info:**")
        st.json(block)
        # QR payload (short JSON)
        payload = {"index": block["index"], "blockHash": block["blockHash"], "fileHash": block["fileHash"]}
        payload_str = json.dumps(payload)
        qr_bytes = generate_qr_bytes(payload_str)
        st.image(qr_bytes, caption="🪪 Verification QR (scan to get payload)")
        st.markdown("[Download QR](%s)" % download_link_bytes(qr_bytes, f"skillchain_qr_{newIndex}.png", "image/png"), unsafe_allow_html=True)
    elif st.button("Issue"):
        st.warning("Please upload a certificate file first.")

# Verify Certificate
elif page == "Verify Certificate":
    st.header("🔍 Verify Certificate")
    st.write("You can either upload a certificate file (we will hash & search the ledger), or paste a QR payload / block hash / file hash.")
    st.subheader("1) Verify by upload")
    verify_upload = st.file_uploader("Upload certificate to verify", type=["pdf","png","jpg","jpeg"], key="verify_upload")
    if st.button("Verify uploaded file"):
        if not verify_upload:
            st.warning("Please upload a file to verify.")
        else:
            raw = verify_upload.read()
            fh = sha256_bytes(raw)
            ledger = load_ledger()
            found = None
            for blk in ledger["blocks"]:
                if blk["fileHash"] == fh:
                    found = blk
                    break
            if found:
                st.success("✅ Verified: File hash found in ledger.")
                st.json(found)
            else:
                st.error("❌ Not verified: No matching file hash in ledger.")

    st.subheader("2) Verify by QR payload or hash")
    raw = st.text_area("Paste QR payload JSON or paste a blockHash / fileHash here")
    if st.button("Verify payload / hash"):
        if not raw.strip():
            st.warning("Paste payload or hash first.")
        else:
            ledger = load_ledger()
            ok = False
            # try JSON parse
            try:
                obj = json.loads(raw)
                for blk in ledger["blocks"]:
                    if blk["index"] == obj.get("index") and blk["blockHash"] == obj.get("blockHash"):
                        st.success("✅ Block found. Certificate verified.")
                        st.json(blk)
                        ok = True
                        break
            except Exception:
                # treat as raw hash
                for blk in ledger["blocks"]:
                    if blk["blockHash"] == raw.strip() or blk["fileHash"] == raw.strip():
                        st.success("✅ Found block matching the provided hash.")
                        st.json(blk)
                        ok = True
                        break
            if not ok:
                st.error("❌ No matching block found in ledger.")

# View Ledger
elif page == "View Ledger":
    st.header("📚 Ledger (blocks)")
    ledger = load_ledger()
    st.write(f"Total blocks: {len(ledger['blocks'])}")
    for blk in ledger["blocks"]:
        with st.expander(f"Block #{blk['index']} — {blk['blockHash'][:12]}..."):
            st.json(blk)
    if st.button("Download ledger.json"):
        data = json.dumps(ledger, indent=2).encode()
        st.markdown("[Download ledger.json](%s)" % download_link_bytes(data, "ledger.json", "application/json"), unsafe_allow_html=True)

# Settings
elif page == "Settings":
    st.header("⚙️ Settings & Persistence")
    st.write("""
    - By default the ledger is stored locally in `ledger.json`.  
    - If you run this app in Google Colab and mount Google Drive, change `LEDGER_FILE` to point to your drive path (example: `/content/drive/MyDrive/skillchain_ledger.json`) and restart the app to persist between sessions.
    """)
    st.write("Optional actions:")
    st.markdown("""
    - Upload a `logo.png` to the repo to show your team logo on the app.
    - Edit `LEDGER_FILE` value in the app source if you want the ledger stored elsewhere.
    """)

# Footer
st.markdown("---")
st.caption("Built by Satvik • SkillChain Hackathon Demo — simulated ledger for demo purposes.")

