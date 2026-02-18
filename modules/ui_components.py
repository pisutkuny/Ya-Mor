import streamlit as st

def big_button(label, key=None, primary=False):
    """
    Renders a big button using custom CSS class. 
    Streamlit buttons are hard to style individually without components, 
    so we rely on global CSS and key-based classes if possible, 
    or just standard Streamlit buttons with 'type="primary"'.
    """
    type_arg = "primary" if primary else "secondary"
    return st.button(label, key=key, type=type_arg, use_container_width=True)

def med_card(med_data, on_click_action=None):
    """
    Renders a medication card with big text.
    med_data: tuple/dict from DB
    """
    # med_data = (id, name, image_path, dosage, frequency, stock, created_at)
    med_id, name, img, dosage, freq, stock, _ = med_data
    
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: #E8F8F5; 
            padding: 25px; 
            border-radius: 20px; 
            border: 3px solid #1ABC9C;
            margin-bottom: 20px;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="margin:0; color:#0E6251; font-size: 2.2rem; border-bottom: none;">💊 {name}</h2>
            <div style="font-size: 1.6rem; margin: 10px 0; color: #145A32;">
                <strong>กินครั้งละ:</strong> {dosage}<br>
                <strong>เหลือ:</strong> <span style="color:#C0392B; font-weight:bold;">{stock}</span> เม็ด
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action Button - Full Width for easier clicking
        if on_click_action:
            if st.button(f"✅ กินแล้ว ({name})", key=f"take_{med_id}", type="primary", use_container_width=True):
                on_click_action(med_id, name)
