// ... existing code ...

def detect_excel_format(file_bytes: bytes):
    """检测Excel文件格式并返回合适的引擎"""
    # 检测文件头信息
    if len(file_bytes) >= 8:
        if file_bytes.startswith(b'PK\x03\x04'):
            return 'xlsx', 'openpyxl'
        elif file_bytes.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
            return 'xls', 'xlrd'

    # 尝试通过文件扩展名判断（作为后备方案）
    return None, None

@router.post("/import/excel")
async def import_excel(
    file: UploadFile = File(...),
    skip_errors: bool = Query(True)
):
    try:
        contents = await file.read()

        # 检测文件格式
        file_format, suggested_engine = detect_excel_format(contents[:8])

        if file_format == 'xlsx':
            logger.info(f"文件头检测为xlsx格式，使用openpyxl引擎")
            engines_to_try = ['openpyxl']
        elif file_format == 'xls':
            logger.info(f"文件头检测为xls格式，使用xlrd引擎")
            engines_to_try = ['xlrd']
        else:
            logger.info(f"无法通过文件头检测格式，尝试所有引擎")
            engines_to_try = ['openpyxl', 'xlrd']

        # 尝试不同的引擎读取Excel
        df_sheet1 = None
        used_engine = None

        for engine in engines_to_try:
            try:
                logger.info(f"开始读取Excel文件: {file.filename}, 使用引擎: {engine}")

                # 使用BytesIO包装文件内容
                file_obj = io.BytesIO(contents)

                if engine == 'openpyxl':
                    df_sheet1 = pd.read_excel(file_obj, sheet_name=0, engine=engine)
                else:
                    df_sheet1 = pd.read_excel(file_obj, sheet_name=0, engine=engine)

                logger.info(f"成功读取Excel文件: {file.filename}, 使用引擎: {engine}")
                used_engine = engine
                break  # 成功读取，跳出循环

            except Exception as e:
                logger.error(f"{engine}引擎读取失败: {str(e)}")
                if engine == engines_to_try[-1]:  # 如果是最后一个引擎
                    raise e
                continue

        if df_sheet1 is None:
            raise HTTPException(status_code=400, detail="无法读取Excel文件")

        # 处理数据...
        return JSONResponse(content={
            "message": "导入成功",
            "filename": file.filename,
            "engine_used": used_engine
        })

    except Exception as e:
        logger.error(f"导入Excel文件失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

// ... existing code ...