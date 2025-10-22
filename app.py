
import streamlit as st
import hashlib
import qrcode
from io import BytesIO

st.set_page_config(page_title='SkillChain', page_icon='🎓', layout='centered')

st.title('🎓 SkillChain — Proof of Learning Network')
st.write('A blockchain-based system to prevent fake certificates and verify student skills securely.')

st.subheader('📤 Upload Your Certificate')
uploaded_file = st.file_uploader('Upload Certificate (PDF / Image)', type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_file:
    st.success('✅ Certificate Uploaded Successfully!')

    # Generate SHA-256 hash (simulating blockchain storage)
    file_bytes = uploaded_file.read()
    hash_value = hashlib.sha256(file_bytes).hexdigest()

    st.write('**🔐 Blockchain Hash (SHA-256):**')
    st.code(hash_value, language='text')

    # Generate a QR code for verification
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(hash_value)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buf = BytesIO()
    img.save(buf, format='PNG')
    st.image(buf.getvalue(), caption='🪪 Verification QR Code')

    st.info('Employers can scan this QR to verify authenticity of the certificate.')

st.markdown('---')
st.caption('🚀 Built by Satvik | SkillChain Hackathon Project')
