import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000
})

export default {
  // 上传公司文件
  async uploadCompanyFiles(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    const response = await api.post('/company/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // 获取公司文件夹列表
  async getCompanyFolders() {
    const response = await api.get('/company/folders')
    return response.data
  },

  // 处理已有的公司文件夹
  async processFolder(folderPath) {
    const formData = new FormData()
    formData.append('folder_path', folderPath)
    const response = await api.post('/company/process-folder', formData)
    return response.data
  },

  // OCR识别身份证图片
  async ocrIdCard(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/ocr/idcard', formData)
    return response.data
  },

  // OCR识别身份证PDF
  async ocrIdCardPdf(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/ocr/idcard-pdf', formData)
    return response.data
  },

  // 上传文件（旧版兼容）
  async uploadFiles(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  // 获取案件列表
  async getCases() {
    const response = await api.get('/cases')
    return response.data
  },

  // 获取单个案件
  async getCase(caseId) {
    const response = await api.get(`/cases/${caseId}`)
    return response.data
  },

  // 更新案件
  async updateCase(caseId, data) {
    const response = await api.put(`/cases/${caseId}`, data)
    return response.data
  },

  // 删除案件
  async deleteCase(caseId) {
    const response = await api.delete(`/cases/${caseId}`)
    return response.data
  },

  // 导出案件Excel
  async exportCaseExcel(caseId) {
    const response = await api.post(`/company/${caseId}/export`, {}, {
      responseType: 'blob'
    })
    return response.data
  },

  // 导出所有案件汇总
  async exportAllCases() {
    const response = await api.post('/company/export-all', {}, {
      responseType: 'blob'
    })
    return response.data
  },

  // 生成文书
  async generateDocument(caseIds, docType) {
    const response = await api.post('/generate/document', {
      case_ids: caseIds,
      doc_type: docType
    }, {
      responseType: 'blob'
    })
    return response.data
  },

  // 批量生成所有文书
  async generateAll(caseIds) {
    const formData = new FormData()
    caseIds.forEach(id => formData.append('case_ids', id))
    const response = await api.post('/generate/all', formData, {
      responseType: 'blob'
    })
    return response.data
  },

  // 获取模板列表
  async getTemplates() {
    const response = await api.get('/templates')
    return response.data
  },

  // AI助手对话（流式响应）
  async *chatAI(message, history = [], context = null, caseId = '') {
    const response = await api.post('/ai/chat', {
      message,
      history,
      context,
      case_id: caseId
    }, {
      responseType: 'stream'
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          try {
            yield JSON.parse(data)
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  },

  // AI助手对话（非流式）
  async chatAISimple(message, history = [], context = null, caseId = '') {
    const response = await api.post('/ai/chat', {
      message,
      history,
      context,
      case_id: caseId,
      stream: false
    })
    return response.data
  },

  // 分析文件内容
  async analyzeFile(fileId, question = '') {
    const response = await api.post('/ai/analyze-file', {
      file_id: fileId,
      question
    })
    return response.data
  },

  // 智能填充表单建议
  async getFormSuggestions(caseId, fieldName) {
    const response = await api.post('/ai/form-suggestions', {
      case_id: caseId,
      field_name: fieldName
    })
    return response.data
  },

  // 下载文件
  downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}

// 解析身份证OCR文本
function parseIdCardText(text) {
  const result = {
    def_name: '',
    def_gender: '',
    def_nation: '',
    def_id: '',
    def_addr: ''
  }

  // 提取身份证号
  const idMatch = text.match(/\d{17}[\dXx]/)
  if (idMatch) {
    result.def_id = idMatch[0].toUpperCase()
  }

  // 提取性别
  if (text.includes('男')) {
    result.def_gender = '男'
  } else if (text.includes('女')) {
    result.def_gender = '女'
  }

  // 提取民族
  const nationMatch = text.match(/(汉|蒙古|回|藏|维吾尔|苗|彝|壮|布依|朝鲜|满|侗|瑶|白|土家|哈尼|哈萨克|傣|黎|傈黎|傈僳|佤|畲|高山|拉祜|水|东乡|纳西|景颇|柯尔克孜|土|达斡尔|仫佬|羌|布朗|撒拉|毛南|仡佬|锡伯|阿昌|普米|塔吉克|怒|乌孜别克|俄罗斯|鄂温克|德昂|保安|裕固|京|塔塔尔|独龙|鄂伦春|赫哲|门巴|珞巴|基诺)族/)
  if (nationMatch) {
    result.def_nation = nationMatch[1]
  }

  // 提取住址
  const addrMatch = text.match(/住址[：:]?\s*(.+?)(?=\n|$|公民身份)/)
  if (addrMatch) {
    result.def_addr = addrMatch[1].trim()
  } else {
    // 尝试匹配省份开头的地址
    const addrMatch2 = text.match(/([一-龥]{2,}省[一-龥\d]+)/)
    if (addrMatch2) {
      result.def_addr = addrMatch2[1]
    }
  }

  // 提取姓名（通常在前几行，2-4个汉字）
  const lines = text.split(/\n|\s+/)
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed && trimmed.length >= 2 && trimmed.length <= 4) {
      if (/^[一-龥]+$/.test(trimmed)) {
        if (!['姓名', '性别', '民族', '出生', '住址', '公民身份号码'].includes(trimmed)) {
          result.def_name = trimmed
          break
        }
      }
    }
  }

  return result
}
