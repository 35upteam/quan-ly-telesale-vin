# ... (Tiếp nối đoạn code của bạn)
                    data = sh_u.get_all_values()
                    users_df = pd.DataFrame(data[1:], columns=data[0])
                    auth = users_df[(users_df['Username'].astype(str) == u_val) & (users_df['Password'].astype(str) == p_val)]
                    
                    if not auth.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = auth.iloc[0]['Tên nhân viên']
                        success = True
                        break
                    else:
                        st.error("Tài khoản hoặc mật khẩu không đúng!")
                        success = True
                        break
                except:
                    if attempt < 2: time.sleep(1); continue
            if success: st.rerun()

# --- 3. GIAO DIỆN SAU KHI ĐĂNG NHẬP ---
else:
    # Header: Xin chào & Đăng xuất (Sử dụng đúng class header-right-container của bạn)
    st.markdown(f'<div class="header-right-container">', unsafe_allow_html=True)
    c_greet, c_logout = st.columns([9, 1])
    with c_greet:
        st.markdown(f'<div class="user-greet" style="text-align: right; padding-top: 5px;">Xin chào <b>{st.session_state["user_name"]}!</b></div>', unsafe_allow_html=True)
    with c_logout:
        if st.button("❌", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    try:
        # Load dữ liệu từ Google Sheets
        sh_data = doc.worksheet("DATA_CAN_HO")
        raw = sh_data.get_all_values()
        h_names = raw[0]
        df_main = pd.DataFrame(raw[1:], columns=h_names).applymap(lambda x: str(x).strip() if x else "")

        # Bộ lọc
        tab1, tab2 = st.tabs(["🔍 Tìm nhanh", "📊 Lọc chi tiết"])
        
        with tab1:
            ci, cb, _ = st.columns([2, 0.8, 3])
            with ci: m_in = st.text_input("Nhập mã căn...", label_visibility="collapsed")
            with cb:
                if st.button("Tìm", key="btn_search"):
                    if m_in:
                        st.session_state['res_df'] = df_main[df_main['Mã đầy đủ'].str.contains(m_in.strip(), case=False)]
                        st.rerun()

        with tab2:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1: ds_toa = st.multiselect("Tòa", sorted([t for t in df_main['Tòa'].unique() if t]))
            with c2: fs = st.selectbox("Từ tầng", LIST_TANG_PHYSICAL, index=4)
            with c3: fe = st.selectbox("Đến tầng", LIST_TANG_PHYSICAL, index=15)
            with c4: tr_sel = st.multiselect("Trục", LIST_TRUC)
            
            if st.button("🚀 Thực hiện lọc", key="btn_filter"):
                tdf = df_main.copy()
                if ds_toa: tdf = tdf[tdf['Tòa'].isin(ds_toa)]
                if tr_sel:
                    tdf['Trục_C'] = tdf['Trục'].apply(lambda x: x.replace(".0", "").zfill(2) if x else "")
                    tdf = tdf[tdf['Trục_C'].isin(tr_sel)]
                idx_s, idx_e = LIST_TANG_PHYSICAL.index(fs), LIST_TANG_PHYSICAL.index(fe)
                tdf = tdf[tdf['Tầng'].isin(LIST_TANG_PHYSICAL[idx_s:idx_e+1])]
                st.session_state['res_df'] = tdf
                st.rerun()

        # Hiển thị danh sách (Sẽ tự động cuộn ngang trên Mobile nhờ CSS div[data-testid="stHorizontalBlock"] của bạn)
        res = st.session_state['res_df']
        if not res.empty:
            st.divider()
            # Dòng tiêu đề
            h_cols = st.columns([1.5, 1.5, 1, 1, 1.8, 3, 0.8])
            titles = ["Mã Căn", "Chủ Nhà", "Loại", "DT", "SĐT", "Ghi chú", "Lưu"]
            for col, title in zip(h_cols, titles):
                col.markdown(f"<div class='header-text'>{title}</div>", unsafe_allow_html=True)
            
            # Danh sách căn hộ
            for i, r in res.iterrows():
                row = st.columns([1.5, 1.5, 1, 1, 1.8, 3, 0.8])
                row[0].write(f"**{r['Mã đầy đủ']}**")
                row[1].write(r['Chủ nhà'])
                row[2].write(r.get('Loại hình', '-'))
                row[3].write(f"{r['Diện tích']}m²")
                
                # Hiển thị SĐT
                sk = f"v_{r['Mã đầy đủ']}"
                if st.session_state.get(sk):
                    row[4].code(r['Số điện thoại'], language="text")
                elif row[4].button("👁️", key=f"eye_{i}"):
                    st.session_state[sk] = True
                    st.rerun()
                
                # Ghi chú & Lưu
                gv = row[5].text_input("G", value=r.get('Ghi chú', ''), key=f"note_{i}", label_visibility="collapsed")
                if row[6].button("💾", key=f"save_{i}"):
                    try:
                        cell = sh_data.find(r['Mã đầy đủ'])
                        sh_data.update_cell(cell.row, h_names.index('Ghi chú') + 1, gv)
                        st.toast(f"Đã lưu {r['Mã đầy đủ']}!")
                    except: st.error("Lỗi!")
                st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
