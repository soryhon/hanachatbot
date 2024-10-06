# 엑셀 시트 선택 및 데이터 처리 로직
def handle_sheet_selection(file_content, sheet_count):
    # 시트 선택 로직 구현
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.text_input("시트 갯수", value=f"{sheet_count}개", disabled=True)
    
    with col2:
        selected_sheets = st.text_input("시트 선택 (예: 1-3, 5)", value="1")
    
    # 선택 버튼을 눌렀을 때만 처리
    if st.button("선택"):
        if validate_sheet_input(selected_sheets):
            parsed_sheets = parse_sheet_selection(selected_sheets, sheet_count)
            if parsed_sheets:
                file_data = extract_sheets_from_excel(file_content, parsed_sheets)
                if file_data:
                    return file_data
                else:
                    st.error(f"선택한 시트에서 데이터를 추출하지 못했습니다.")
                    return None
            else:
                st.error(f"잘못된 시트 선택입니다: {selected_sheets}")
                return None
        else:
            st.error(f"잘못된 입력 형식입니다. 숫자와 '-', ','만 입력할 수 있습니다.")
            return None

# 엑셀 파일에서 시트 선택하고 데이터를 추출하는 부분
def handle_file_selection(file_path, file_content, file_type, idx):
    if file_type == 'xlsx':
        # 엑셀 파일을 로드하고 시트 개수를 확인
        wb = openpyxl.load_workbook(file_content)
        sheet_count = len(wb.sheetnames)

        # 시트 선택 로직 처리
        if sheet_count > 0:
            file_data_dict = handle_sheet_selection(file_content, sheet_count)  # 시트 선택

            if file_data_dict:
                titles = [st.session_state['rows'][idx]['제목']]
                html_report = generate_html_report_with_title(titles, [file_data_dict])
                st.session_state['html_report'] = html_report  # HTML 세트를 세션 상태에 저장
                return file_data_dict
            else:
                st.error(f"선택한 시트에서 데이터를 찾을 수 없습니다.")
        else:
            st.error("엑셀 파일에서 시트를 찾을 수 없습니다.")
    else:
        return extract_data_from_file(file_content, file_type)
