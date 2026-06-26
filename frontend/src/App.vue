<template>
  <div class="app-container" v-loading="globalLoading" :element-loading-text="loadingText" element-loading-background="rgba(255, 255, 255, 0.9)">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="logo">
        <el-icon><Document /></el-icon>
        <span>法律文书自动生成系统</span>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" simple class="steps">
        <el-step title="选择公司" />
        <el-step title="确认数据" />
        <el-step title="生成文书" />
      </el-steps>

      <!-- 步骤1: 导入文件 -->
      <el-card v-if="currentStep === 0" class="step-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><FolderOpened /></el-icon>
            <span>步骤1：导入公司文件</span>
          </div>
        </template>

        <!-- 方式选择 -->
        <el-tabs v-model="importMode" class="import-tabs">
          <el-tab-pane label="选择已有文件夹" name="existing">
            <div class="folder-section">
              <el-button type="primary" @click="loadFolders" :loading="loadingFolders">
                <el-icon><Refresh /></el-icon>
                刷新列表
              </el-button>
            </div>

            <el-table :data="folders" v-loading="loadingFolders" highlight-current-row class="folder-table">
              <el-table-column prop="name" label="公司名称" min-width="100" />
              <el-table-column prop="file_count" label="文件数" width="80" align="center" />
              <el-table-column label="文件类型" min-width="300">
                <template #default="{ row }">
                  <el-tag v-for="(count, type) in row.file_types" :key="type"
                          :type="getFileTypeTag(type)" size="small" class="type-tag">
                    {{ getFileTypeLabel(type) }}: {{ count }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" align="center">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click.stop="selectAndProcess(row)">
                    选择
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="上传新文件夹" name="upload">
            <!-- 文件上传区域 -->
            <el-upload
              ref="uploadRef"
              class="upload-area"
              drag
              multiple
              directory
              webkitdirectory
              :auto-upload="false"
              :on-change="handleFileChange"
              :file-list="fileList"
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件夹拖到此处，或<em>点击选择文件夹</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持选择整个文件夹，系统会自动过滤无用文件
                </div>
              </template>
            </el-upload>

            <!-- 已选文件列表 -->
            <div v-if="fileList.length > 0" class="selected-files">
              <div class="files-header">
                <span>已选择 {{ fileList.length }} 个文件</span>
                <el-button type="danger" size="small" @click="clearFiles">清空</el-button>
              </div>
              <el-scrollbar height="200px">
                <div v-for="(file, index) in fileList.slice(0, 20)" :key="index" class="file-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ file.name }}</span>
                </div>
                <div v-if="fileList.length > 20" class="file-item" style="color: #999;">
                  ... 还有 {{ fileList.length - 20 }} 个文件
                </div>
              </el-scrollbar>
            </div>

            <!-- 处理按钮 -->
            <div class="process-actions">
              <el-button type="primary" size="large" @click="processFiles" :loading="processing">
                <el-icon><Check /></el-icon>
                开始处理
              </el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="批量生成律师函" name="batch_lawyer">
            <div class="batch-lawyer-section">
              <!-- 上传XLSX区域 -->
              <div class="batch-upload-area">
                <el-upload
                  ref="xlsxUploadRef"
                  class="batch-xlsx-upload"
                  drag
                  :auto-upload="false"
                  :on-change="handleXlsxChange"
                  :file-list="xlsxFileList"
                  :show-file-list="false"
                  accept=".xlsx"
                  :limit="1"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    将批量数据Excel拖到此处，或<em>点击选择文件</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      第一行为表头（列名与模板变量对应），每行为一份文书的数据
                    </div>
                  </template>
                </el-upload>
                <div v-if="xlsxFileList.length > 0" style="text-align: center; margin-top: 12px;">
                  <el-tag type="primary" size="large" closable @close="clearXlsxFile">
                    <el-icon><Document /></el-icon>
                    {{ xlsxFileList[0]?.name }}
                  </el-tag>
                </div>
                <div class="process-actions">
                  <el-button type="primary" size="large" @click="previewXlsx" :loading="previewingXlsx" :disabled="xlsxFileList.length === 0">
                    <el-icon><View /></el-icon>
                    预览数据
                  </el-button>
                </div>
              </div>

              <!-- 模板变量提示 -->
              <div v-if="templateVariables.length > 0" class="template-vars-hint">
                <el-alert type="info" :closable="false" show-icon>
                  <template #title>
                    模板变量参考（共{{ templateVariables.length }}个）
                  </template>
                  <template #default>
                    <div class="var-tags">
                      <el-tag v-for="v in templateVariables" :key="v" size="small" type="info" class="var-tag-item">
                        {{ v }}
                      </el-tag>
                    </div>
                  </template>
                </el-alert>
              </div>

              <!-- 数据预览表格 -->
              <div v-if="xlsxPreviewData.columns.length > 0" class="xlsx-preview">
                <div class="preview-header">
                  <h4>
                    <el-icon><DataAnalysis /></el-icon>
                    数据预览（共{{ xlsxPreviewData.row_count }}条记录）
                  </h4>
                  <el-button type="success" size="large" @click="batchGenerateDocuments" :loading="batchGenerating">
                    <el-icon><Download /></el-icon>
                    一键生成律师函
                  </el-button>
                </div>
                <el-table :data="xlsxPreviewData.rows" border stripe size="small" max-height="400" style="width: 100%">
                  <el-table-column
                    v-for="col in xlsxPreviewData.columns"
                    :key="col"
                    :prop="col"
                    :label="col"
                    min-width="140"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="一键生成执行材料" name="batch_execution">
            <div class="batch-lawyer-section">
              <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px;">
                <template #title>
                  功能开发中，请告知具体步骤
                </template>
              </el-alert>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 步骤2: 确认数据 - 全部在一个页面上 -->
      <el-card v-if="currentStep === 1" class="step-card" shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="card-header">
              <el-icon class="header-icon"><Edit /></el-icon>
              <span>步骤2：确认提取数据</span>
            </div>
            <el-tag type="success" size="large" effect="dark" class="company-tag">
              {{ caseData.company_info.target_company || '待识别公司' }}
            </el-tag>
          </div>
        </template>

        <el-scrollbar height="calc(100vh - 300px)">
        <!-- 公司信息 -->
        <div class="section-block">
          <div class="section-title"><el-icon><OfficeBuilding /></el-icon> 公司信息</div>
          <el-form :model="caseData.company_info" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="企业名称">
                  <el-input v-model="caseData.company_info.target_company" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="公司简称">
                  <el-input v-model="caseData.company_info.company_abbr" placeholder="手动填写" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="法定代表人">
                  <el-input v-model="caseData.company_info.legal_representative" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="注册资本">
                  <el-input v-model="caseData.company_info.company_capital" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="住所">
                  <el-input v-model="caseData.company_info.company_addr" type="textarea" :rows="2" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="成立日期">
                  <el-input v-model="caseData.company_info.company_establish" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="登记机关">
                  <el-input v-model="caseData.company_info.company_reg" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="核准日期">
                  <el-input v-model="caseData.company_info.company_cancel_apply" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="出资状态">
                  <el-select v-model="caseData.company_info.capital_status" placeholder="手动填写" style="width: 100%">
                    <el-option label="未实缴" value="未实缴" />
                    <el-option label="部分实缴" value="部分实缴" />
                    <el-option label="已实缴" value="已实缴" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="认缴日期">
                  <el-input v-model="caseData.company_info.subscribe_date" placeholder="手动填写" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 被告/股东信息 -->
        <div class="section-block">
          <div class="section-title"><el-icon><User /></el-icon> 被告/股东信息</div>
          <div v-for="(defendant, index) in caseData.defendants" :key="index" class="defendant-card">
            <div class="defendant-header">
              <h4>被告{{ index + 1 }} {{ defendant.is_legal_rep ? '(法定代表人)' : '(股东)' }}</h4>
              <el-button v-if="idCardImages[index]" type="primary" size="small" @click="showIdCardImage(index)">
                <el-icon><View /></el-icon>
                查看身份证
              </el-button>
            </div>
            <el-form :model="defendant" label-width="80px">
              <el-row :gutter="20">
                <el-col :span="4">
                  <el-form-item label="姓名">
                    <el-input v-model="defendant.def_name" />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="性别">
                    <el-select v-model="defendant.def_gender" style="width: 100%">
                      <el-option label="男" value="男" />
                      <el-option label="女" value="女" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="民族">
                    <el-input v-model="defendant.def_nation" />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="认缴额(万)">
                    <el-input v-model="defendant.def_subscribe_amount" />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="实缴额(万)">
                    <el-input v-model="defendant.def_paid_amount" />
                  </el-form-item>
                </el-col>
                <el-col :span="4">
                  <el-form-item label="持股比例">
                    <el-input v-model="defendant.def_share" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="身份证号">
                    <el-input v-model="defendant.def_id" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="电话">
                    <el-input v-model="defendant.def_tel" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="住址">
                    <el-input v-model="defendant.def_addr" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
            <div class="defendant-card-footer">
              <el-button type="danger" size="small" @click="removeDefendant(index)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
          <el-button type="primary" plain @click="addDefendant">
            <el-icon><Plus /></el-icon>
            添加被告
          </el-button>
        </div>

        <!-- 合同信息 -->
        <div class="section-block">
          <div class="section-title"><el-icon><Tickets /></el-icon> 合同信息</div>

          <!-- 额度合同 -->
          <div class="contract-subsection">
            <div class="subsection-header">
              <span>额度合同（共{{ caseData.loan_contracts.quota_count }}份）</span>
            </div>
            <el-table :data="caseData.loan_contracts.quota_contracts" size="small" border v-if="caseData.loan_contracts.quota_contracts.length > 0">
              <el-table-column prop="contract_no" label="合同编号" min-width="200">
                <template #default="{ row }">
                  <el-input v-model="row.contract_no" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="contract_date" label="签订日期" width="150">
                <template #default="{ row }">
                  <el-input v-model="row.contract_date" size="small" placeholder="手动填写" />
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无额度合同数据" :image-size="60" />
          </div>

          <!-- 借款合同明细 -->
          <div class="contract-subsection">
            <div class="subsection-header">
              <span>借款合同明细（共{{ caseData.loan_contracts.loan_count }}份）</span>
            </div>
            <el-table :data="caseData.loan_contracts.loan_contracts" size="small" border>
              <el-table-column prop="jieju_no" label="借据号" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.jieju_no" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="contract_no" label="合同编号" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.contract_no" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="contract_date" label="签订日期" width="130">
                <template #default="{ row }">
                  <el-input v-model="row.contract_date" size="small" placeholder="手动填写" />
                </template>
              </el-table-column>
              <el-table-column prop="principal" label="本金" width="100">
                <template #default="{ row }">
                  <el-input v-model="row.principal" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="total_principal" label="欠款总本金" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.total_principal" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="rate" label="利率" width="90">
                <template #default="{ row }">
                  <el-input v-model="row.rate" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="penalty_rate" label="罚息利率" width="100">
                <template #default="{ row }">
                  <el-input v-model="row.penalty_rate" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="standard_penalty_rate" label="规范罚息利率" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.standard_penalty_rate" size="small" />
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 借款合同汇总 -->
          <div class="contract-subsection" v-if="loanSummary.length > 0">
            <div class="subsection-header">
              <span>借款合同汇总（按规范罚息利率分组）</span>
            </div>
            <el-table :data="loanSummary" size="small" border>
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="principal" label="欠款总本金合计" width="140">
                <template #default="{ row }">
                  {{ row.principal }}元
                </template>
              </el-table-column>
              <el-table-column prop="rate" label="利率" width="100" />
              <el-table-column prop="penalty_rate" label="罚息利率" width="100" />
              <el-table-column prop="standard_penalty_rate" label="规范罚息利率" width="120">
                <template #default="{ row }">
                  <el-tag type="warning">{{ row.standard_penalty_rate }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="合同数" width="80" />
            </el-table>
          </div>
        </div>

        <!-- 债务信息 -->
        <div class="section-block">
          <div class="section-title"><el-icon><Money /></el-icon> 债务信息</div>
          <el-form :model="caseData.debt_info" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="截止日期">
                  <el-input v-model="caseData.debt_info.end_date" placeholder="如：2026年3月3日" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="贷款本金合计">
                  <el-input v-model="caseData.debt_info.loan_total">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="欠付本金">
                  <el-input v-model="caseData.debt_info.principal">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="利息">
                  <el-input v-model="caseData.debt_info.interest">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="罚息">
                  <el-input v-model="caseData.debt_info.penalty_cutoff">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="保全金额">
                  <el-input v-model="caseData.debt_info.guarantee_amount">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="取整保全金额">
                  <el-input v-model="caseData.debt_info.guarantee_amount_rounded">
                    <template #append>元</template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 案件信息 -->
        <div class="section-block">
          <div class="section-title"><el-icon><Briefcase /></el-icon> 案件信息</div>
          <el-form :model="caseData.case_info" label-width="130px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="案由">
                  <el-select v-model="caseData.case_info.case_reason" style="width: 100%">
                    <el-option label="清算责任纠纷" value="清算责任纠纷" />
                    <el-option label="损害公司债权人利益责任纠纷" value="损害公司债权人利益责任纠纷" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="受理法院">
                  <el-input v-model="caseData.case_info.court_name" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="注销文件">
                  <el-select v-model="caseData.case_info.cancel_doc" placeholder="请选择" style="width: 100%">
                    <el-option label="清算报告" value="清算报告" />
                    <el-option label="简易注销全体投资人承诺书" value="简易注销全体投资人承诺书" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="委托律师">
                  <el-input v-model="caseData.lawer" placeholder="手动填写" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <!-- 证据目录页码 -->
        <div class="section-block">
          <div class="section-title"><el-icon><Document /></el-icon> 证据目录页码</div>
          <el-form :model="caseData.case_info" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="放款流水页数">
                  <el-input v-model="caseData.case_info.page_number1" placeholder="手动填写" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="还款流水页数">
                  <el-input v-model="caseData.case_info.page_number2" placeholder="手动填写" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="金额计算表页数" label-width="110px">
                  <el-input v-model="caseData.case_info.page_number3" placeholder="手动填写" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>


        </el-scrollbar>

        <div class="step-actions">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button type="primary" @click="saveAndGenerate">
            <el-icon><Check /></el-icon>
            保存并生成文书
          </el-button>
        </div>
      </el-card>

      <!-- 步骤3: 生成文书 -->
      <el-card v-if="currentStep === 2" class="step-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Document /></el-icon>
            <span>步骤3：生成法律文书</span>
          </div>
        </template>

        <!-- 诉讼材料 -->
        <div class="doc-section">
          <div class="doc-section-header">
            <span class="doc-section-title">诉讼材料</span>
            <el-button type="primary" link @click="toggleLitigationAll">
              {{ allLitigationSelected ? '取消全选' : '全选' }}
            </el-button>
          </div>
          <el-checkbox-group v-model="selectedDocs" class="doc-checkbox-group">
            <el-checkbox v-for="opt in litigationOptions" :key="opt.value" :label="opt.value">
              {{ opt.label }}
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <!-- 执行材料 -->
        <div class="doc-section">
          <div class="doc-section-header">
            <span class="doc-section-title">执行材料</span>
            <el-button type="primary" link @click="toggleExecutionAll">
              {{ allExecutionSelected ? '取消全选' : '全选' }}
            </el-button>
          </div>
          <el-checkbox-group v-model="selectedDocs" class="doc-checkbox-group">
            <el-checkbox v-for="opt in executionOptions" :key="opt.value" :label="opt.value">
              {{ opt.label }}
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <div class="step-actions">
          <el-button @click="currentStep = 1">上一步</el-button>
          <el-button type="success" @click="exportCompanyData" :loading="exporting">
            <el-icon><Download /></el-icon>
            公司数据
          </el-button>
          <el-button type="primary" @click="generateDocuments" :loading="generating">
            <el-icon><Download /></el-icon>
            生成选中文书
          </el-button>
        </div>

        <!-- 生成结果 -->
        <div v-if="generatedFiles.length > 0" class="generated-files">
          <h4>已生成文书：</h4>
          <el-table :data="generatedFiles" size="small">
            <el-table-column prop="name" label="文书名称" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="downloadFile(row)">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </main>

    <!-- 身份证图片预览对话框 -->
    <el-dialog v-model="showIdCardDialog" title="身份证图片" width="800px" top="5vh">
      <div class="idcard-preview">
        <img :src="currentIdCardImage" alt="身份证" style="max-width: 100%; max-height: 70vh;" />
      </div>
      <div class="idcard-tips">
        <el-alert title="请根据图片内容填写左侧表单" type="info" :closable="false" />
      </div>
    </el-dialog>

    <!-- AI助手 -->
    <AIAssistant :context-data="caseData" :case-id="caseData.id" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import AIAssistant from './components/AIAssistant.vue'

// 当前步骤
const currentStep = ref(0)

// 导入方式
const importMode = ref('existing')

// 文件上传相关
const uploadRef = ref(null)
const fileList = ref([])
const processing = ref(false)

// 全局加载状态
const globalLoading = ref(false)
const loadingText = ref('正在处理...')

// 文件夹列表
const folders = ref([])
const loadingFolders = ref(false)

// 身份证图片
const idCardImages = ref({})
const showIdCardDialog = ref(false)
const currentIdCardImage = ref('')

// 板块显示/隐藏控制
const sectionVisible = reactive({
  lawyerLetter: true,
  execution: true
})

// 案件数据
const caseData = reactive({
  id: '',
  lawer: '',  // 委托律师
  company_info: {
    target_company: '',
    company_abbr: '',
    legal_representative: '',
    company_capital: '',
    company_establish: '',
    company_addr: '',
    company_reg: '',
    company_cancel_apply: '',
    capital_status: '',
    subscribe_date: ''
  },
  defendants: [],
  debt_info: {
    loan_total: '',
    principal: '',
    interest: '',
    penalty_cutoff: '',
    cutoff_date: '',
    end_date: '',
    start_date: '',
    guarantee_amount: '',
    guarantee_amount_rounded: ''
  },
  loan_contracts: {
    quota_contracts: [],
    loan_contracts: [],
    quota_count: 0,
    loan_count: 0
  },
  case_info: {
    case_reason: '',
    court_name: '',
    case_number: '',
    judgment_document: '',
    page_number1: '',
    page_number2: '',
    page_number3: '',
    cancel_doc: ''
  },
  lawyer_letter_info: {
    recipient: '',
    amount: '',
    case_number: '',
    date: ''
  },
  execution_info: {
    judgment_case_number: '',
    judgment_principal: '',
    judgment_interest: '',
    court_fee: '',
    preservation_fee: '',
    notice_fee: ''
  }
})

// 计算贷款本金合计
const loanTotalComputed = computed(() => {
  let total = 0
  for (const loan of caseData.loan_contracts.loan_contracts) {
    const p = parseFloat(loan.principal) || 0
    total += p
  }
  return total.toFixed(2)
})

// 计算借款合同汇总（按规范罚息利率分组）
const loanSummary = computed(() => {
  const groups = {}
  for (const loan of caseData.loan_contracts.loan_contracts) {
    const key = loan.standard_penalty_rate || '24.00%'
    if (!groups[key]) {
      groups[key] = {
        standard_penalty_rate: key,
        rate: loan.rate,
        penalty_rate: loan.penalty_rate,
        principal: 0,
        count: 0
      }
    }
    groups[key].principal += parseFloat(loan.total_principal || loan.principal) || 0
    groups[key].count += 1
  }
  // 格式化本金
  const result = []
  for (const key in groups) {
    result.push({
      ...groups[key],
      principal: groups[key].principal.toFixed(2)
    })
  }
  return result
})

// 计算取整保全金额
const guaranteeAmountRounded = computed(() => {
  const amount = parseFloat(caseData.debt_info.guarantee_amount)
  if (isNaN(amount) || amount === 0) return '0.00'
  const floorValue = Math.floor(amount / 1000) * 1000
  const thousandsDigit = Math.floor(floorValue / 1000) % 10
  let result
  if (thousandsDigit < 5) {
    result = Math.floor(floorValue / 10000) * 10000
  } else {
    result = floorValue
  }
  return result.toFixed(2)
})

// 保全金额变化时自动计算取整保全金额（用户可手动修改）
watch(() => caseData.debt_info.guarantee_amount, (newVal) => {
  if (newVal && !isNaN(parseFloat(newVal))) {
    caseData.debt_info.guarantee_amount_rounded = guaranteeAmountRounded.value
  }
})

// 诉讼材料可选文书（1-10）
const litigationOptions = computed(() => {
  const options = [
    { label: '证据目录', value: '证据目录' },
    { label: '保函', value: '保函' },
    { label: '保全申请书', value: '保全申请书' },
    { label: '诉讼授权委托书', value: '诉讼授权委托书' },
    { label: '诉讼文书送达地址确认', value: '诉讼文书送达地址确认' },
    { label: '诉讼公函', value: '诉讼公函' },
    { label: '诉讼费退费账号', value: '诉讼费退费账号' },
    { label: '网络查控申请书', value: '网络查控申请书' },
  ]
  const reason = caseData.case_info.case_reason
  if (reason) {
    options.unshift({ label: `起诉状（${reason}）`, value: `起诉状-${reason}` })
  }
  return options
})

// 执行材料可选文书（10-14，律师函由批量上传单独生成）
const executionOptions = computed(() => {
  return [
    { label: '执行公函', value: '执行公函' },
    { label: '执行款收款账户', value: '执行款收款账户' },
    { label: '执行授权委托书', value: '执行授权委托书' },
    { label: '执行申请书', value: '执行申请书' },
    { label: '执行送达地址确认', value: '执行送达地址确认' },
  ]
})

// 所有可选文书（合并）
const docCheckboxOptions = computed(() => {
  return [...litigationOptions.value, ...executionOptions.value]
})

// 选中要生成的文书
const selectedDocs = ref([])

// 诉讼材料是否全选
const allLitigationSelected = computed(() => {
  const litValues = litigationOptions.value.map(o => o.value)
  return litValues.length > 0 && litValues.every(v => selectedDocs.value.includes(v))
})

// 切换诉讼材料全选/取消全选
function toggleLitigationAll() {
  const litValues = litigationOptions.value.map(o => o.value)
  if (allLitigationSelected.value) {
    selectedDocs.value = selectedDocs.value.filter(v => !litValues.includes(v))
  } else {
    const newSet = new Set([...selectedDocs.value, ...litValues])
    selectedDocs.value = [...newSet]
  }
}

// 执行材料是否全选
const allExecutionSelected = computed(() => {
  const execValues = executionOptions.value.map(o => o.value)
  return execValues.length > 0 && execValues.every(v => selectedDocs.value.includes(v))
})

// 切换执行材料全选/取消全选
function toggleExecutionAll() {
  const execValues = executionOptions.value.map(o => o.value)
  if (allExecutionSelected.value) {
    selectedDocs.value = selectedDocs.value.filter(v => !execValues.includes(v))
  } else {
    const newSet = new Set([...selectedDocs.value, ...execValues])
    selectedDocs.value = [...newSet]
  }
}

// 初始化选中状态：默认全选（含起诉状）
function initSelectedDocs() {
  selectedDocs.value = docCheckboxOptions.value.map(opt => opt.value)
}

// 案由变更时同步更新选中列表中的起诉状选项
watch(() => caseData.case_info.case_reason, (newReason, oldReason) => {
  const oldKey = oldReason ? `起诉状-${oldReason}` : null
  const newKey = newReason ? `起诉状-${newReason}` : null
  if (oldKey) {
    const idx = selectedDocs.value.indexOf(oldKey)
    if (idx >= 0) selectedDocs.value.splice(idx, 1)
  }
  if (newKey && !selectedDocs.value.includes(newKey)) {
    selectedDocs.value.unshift(newKey)
  }
})

// 初始化默认全选
initSelectedDocs()

// 生成状态
const generating = ref(false)
const generatedFiles = ref([])
const exporting = ref(false)

// 批量生成律师函相关
const xlsxUploadRef = ref(null)
const xlsxFileList = ref([])
const xlsxPreviewData = reactive({
  columns: [],
  rows: [],
  row_count: 0
})
const templateVariables = ref([])
const previewingXlsx = ref(false)
const batchGenerating = ref(false)

// 文件类型映射
const FILE_TYPE_MAP = {
  'public_report': { label: '公示系统', tag: 'success' },
  'id_card_front': { label: '身份证正面', tag: 'primary' },
  'id_card_back': { label: '身份证反面', tag: 'primary' },
  'quota_contract': { label: '额度合同', tag: 'warning' },
  'loan_contract': { label: '借款合同', tag: 'warning' },
  'loan_flow': { label: '放款流水', tag: 'info' },
  'repay_flow': { label: '还款流水', tag: 'info' },
  'guarantee_contract': { label: '担保合同', tag: '' },
  'calc_logic': { label: '金额计算Excel', tag: 'danger' },
  'other': { label: '其他', tag: 'info' }
}

function getFileTypeTag(type) {
  return FILE_TYPE_MAP[type]?.tag || 'info'
}

function getFileTypeLabel(type) {
  return FILE_TYPE_MAP[type]?.label || type
}

// 文件选择处理
function handleFileChange(file, list) {
  fileList.value = list
}

// 清空文件列表
function clearFiles() {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

// 处理上传的文件
async function processFiles() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  processing.value = true
  ElMessage.info('正在处理文件，请耐心等待...')

  try {
    const formData = new FormData()
    fileList.value.forEach(file => {
      formData.append('files', file.raw)
    })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 300000)

    const response = await fetch('/api/company/upload', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    const result = await response.json()

    if (result.success) {
      Object.assign(caseData, result.case)
      clearFiles()
      currentStep.value = 1
      ElMessage.success('解析完成！')
    } else {
      throw new Error(result.message || '解析失败')
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      ElMessage.error('处理超时，请重试')
    } else {
      ElMessage.error('处理失败: ' + error.message)
    }
  } finally {
    processing.value = false
  }
}

// 加载文件夹列表
async function loadFolders() {
  loadingFolders.value = true
  try {
    const response = await fetch('/api/company/folders')
    const result = await response.json()
    folders.value = result.folders || []
  } catch (error) {
    ElMessage.error('加载文件夹列表失败: ' + error.message)
  } finally {
    loadingFolders.value = false
  }
}

// 选择并处理文件夹
async function selectAndProcess(row) {
  globalLoading.value = true
  loadingText.value = `正在处理: ${row.name}，请稍候...`

  try {
    const response = await fetch('/api/company/process-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `folder_path=${encodeURIComponent(row.path)}`
    })

    const result = await response.json()

    if (result.success) {
      Object.assign(caseData, result.case)
      await loadIdCardImages(row.path)
      currentStep.value = 1
      ElMessage.success('数据提取完成！')
    } else {
      throw new Error(result.message || '解析失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    globalLoading.value = false
  }
}

// 加载身份证图片
async function loadIdCardImages(folderPath) {
  idCardImages.value = {}
  for (let i = 0; i < caseData.defendants.length; i++) {
    const defName = caseData.defendants[i].def_name
    if (defName) {
      try {
        const response = await fetch(`/api/company/idcard-image?folder=${encodeURIComponent(folderPath)}&name=${encodeURIComponent(defName)}`)
        if (response.ok) {
          const blob = await response.blob()
          idCardImages.value[i] = URL.createObjectURL(blob)
        }
      } catch (e) {
        console.log('未找到身份证图片:', defName)
      }
    }
  }
}

// 显示身份证图片
function showIdCardImage(index) {
  if (idCardImages.value[index]) {
    currentIdCardImage.value = idCardImages.value[index]
    showIdCardDialog.value = true
  }
}

// 当天日期格式化
function getTodayString() {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}年${m}月${d}日`
}

// 删除被告
function removeDefendant(index) {
  caseData.defendants.splice(index, 1)
}

// 添加被告
function addDefendant() {
  caseData.defendants.push({
    def_name: '',
    def_gender: '',
    def_nation: '',
    def_id: '',
    def_addr: '',
    def_tel: '',
    def_subscribe_amount: '',
    def_paid_amount: '',
    def_share: '',
    is_legal_rep: false
  })
}

// 保存并进入生成步骤
async function saveAndGenerate() {
  try {
    caseData.debt_info.loan_total = loanTotalComputed.value

    await fetch(`/api/cases/${caseData.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_info: caseData.company_info,
        defendants: caseData.defendants,
        debt_info: caseData.debt_info,
        case_info: caseData.case_info,
        lawyer_letter_info: caseData.lawyer_letter_info,
        lawer: caseData.lawer
      })
    })

    ElMessage.success('数据已保存')
    currentStep.value = 2
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

// 生成文书
async function generateDocuments() {
  if (selectedDocs.value.length === 0) {
    ElMessage.warning('请至少选择一种文书')
    return
  }

  generating.value = true
  generatedFiles.value = []

  try {
    const response = await fetch('/api/generate/selected', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_ids: [caseData.id],
        doc_types: selectedDocs.value
      })
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const contentDisposition = response.headers.get('content-disposition')
      let filename = '法律文书.zip'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
        if (match) filename = decodeURIComponent(match[1])
      }

      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      window.URL.revokeObjectURL(url)

      generatedFiles.value = selectedDocs.value.map(d => ({ name: d, url: '' }))
      ElMessage.success('文书生成完成，已下载zip文件')
    } else {
      throw new Error('生成失败')
    }
  } catch (error) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    generating.value = false
  }
}

// 下载文件
function downloadFile(file) {
  const link = document.createElement('a')
  link.href = file.url
  link.download = `${file.name}.docx`
  link.click()
}

// 批量生成律师函 - XLSX文件选择
function handleXlsxChange(file, list) {
  xlsxFileList.value = list
  // 清空之前的预览数据
  xlsxPreviewData.columns = []
  xlsxPreviewData.rows = []
  xlsxPreviewData.row_count = 0
  templateVariables.value = []
}

function clearXlsxFile() {
  xlsxFileList.value = []
  xlsxUploadRef.value?.clearFiles()
  xlsxPreviewData.columns = []
  xlsxPreviewData.rows = []
  xlsxPreviewData.row_count = 0
  templateVariables.value = []
}

// 批量生成文书 - 预览XLSX数据
async function previewXlsx() {
  if (xlsxFileList.value.length === 0) {
    ElMessage.warning('请先选择XLSX文件')
    return
  }

  previewingXlsx.value = true
  try {
    const file = xlsxFileList.value[0].raw
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', '律师函')
    const response = await fetch('/api/batch/preview-xlsx', {
      method: 'POST',
      body: fd
    })

    const result = await response.json()

    if (result.success) {
      xlsxPreviewData.columns = result.columns
      xlsxPreviewData.rows = result.rows
      xlsxPreviewData.row_count = result.row_count
      templateVariables.value = result.template_variables || []
      ElMessage.success(`读取成功，共 ${result.row_count} 条记录`)
    } else {
      throw new Error(result.message || '读取失败')
    }
  } catch (error) {
    ElMessage.error('预览失败: ' + error.message)
  } finally {
    previewingXlsx.value = false
  }
}

// 批量生成文书 - 一键生成
async function batchGenerateDocuments() {
  if (xlsxFileList.value.length === 0) {
    ElMessage.warning('请先选择XLSX文件')
    return
  }

  if (xlsxPreviewData.row_count === 0) {
    ElMessage.warning('请先预览数据')
    return
  }

  batchGenerating.value = true
  try {
    const file = xlsxFileList.value[0].raw
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', '律师函')
    const response = await fetch('/api/batch/generate', {
      method: 'POST',
      body: fd
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const contentDisposition = response.headers.get('content-disposition')
      let filename = '批量生成文书.docx'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
        if (match) filename = decodeURIComponent(match[1])
      }

      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      window.URL.revokeObjectURL(url)

      ElMessage.success(`成功生成 ${xlsxPreviewData.row_count} 份文书`)
    } else {
      throw new Error('生成失败')
    }
  } catch (error) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    batchGenerating.value = false
  }
}

// 导出公司数据Excel
async function exportCompanyData() {
  exporting.value = true
  try {
    const response = await fetch(`/api/company/${caseData.id}/export`, {
      method: 'POST'
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const contentDisposition = response.headers.get('content-disposition')
      let filename = `database_element_${caseData.company_info.target_company || caseData.id}.xlsx`
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
        if (match) filename = decodeURIComponent(match[1])
      }

      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      window.URL.revokeObjectURL(url)

      ElMessage.success('公司数据Excel已下载')
    } else {
      throw new Error('导出失败')
    }
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  } finally {
    exporting.value = false
  }
}

// 初始化
onMounted(() => {
  loadFolders()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  background: transparent;
}

.header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 24px 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.logo .el-icon {
  font-size: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 8px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.main {
  padding: 32px 48px;
  max-width: 1400px;
  margin: 0 auto;
}

.steps {
  margin-bottom: 32px;
  background: white;
  padding: 20px 32px;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.step-card {
  margin-bottom: 24px;
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.step-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-bottom: 1px solid #eee;
  padding: 18px 24px;
  font-weight: 600;
  font-size: 16px;
  color: #1a1a2e;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.doc-section {
  margin-bottom: 20px;
}

.doc-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.doc-section-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.header-icon {
  font-size: 20px;
  color: #667eea;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8edff 100%);
  padding: 8px;
  border-radius: 8px;
}

.company-tag {
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 8px;
}

.step-card :deep(.el-card__body) {
  padding: 28px;
}

.step-actions {
  margin-top: 36px;
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.step-actions .el-button {
  min-width: 140px;
  border-radius: 10px;
  font-weight: 500;
}

/* 新增：板块样式 */
.section-block {
  margin-bottom: 24px;
  padding: 24px;
  background: #fafbfc;
  border-radius: 12px;
  border: 1px solid #eee;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #667eea;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #667eea;
  font-size: 18px;
}

.contract-subsection {
  margin-top: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.subsection-header {
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.folder-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
}

.folder-table {
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
}

.folder-table :deep(.el-table__header th) {
  background: #f8f9fa;
  font-weight: 600;
  color: #1a1a2e;
}

.folder-table :deep(.el-table__row:hover > td) {
  background: #f0f4ff !important;
}

.type-tag {
  margin: 3px;
  border-radius: 6px;
  font-weight: 500;
}

.defendant-card {
  padding: 24px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #eaeaea;
  transition: all 0.3s ease;
}

.defendant-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: #667eea;
}

.defendant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #eee;
}

.defendant-header h4 {
  color: #1a1a2e;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.defendant-card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.section-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.doc-checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
}

.doc-checkbox-group :deep(.el-checkbox) {
  background: white;
  padding: 16px 20px;
  border-radius: 10px;
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  margin: 0;
  height: auto;
}

.doc-checkbox-group :deep(.el-checkbox:hover) {
  border-color: #667eea;
  box-shadow: 0 2px 10px rgba(102, 126, 234, 0.15);
}

.doc-checkbox-group :deep(.el-checkbox.is-checked) {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
}

.doc-checkbox-group :deep(.el-checkbox__label) {
  font-weight: 500;
  color: #333;
}

.generated-files {
  margin-top: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f0fff4 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #c3e6cb;
}

.generated-files h4 {
  color: #28a745;
  margin-bottom: 16px;
  font-weight: 600;
}

.idcard-preview {
  text-align: center;
  padding: 20px;
}

.idcard-tips {
  margin-top: 15px;
}

/* 上传区域样式 */
.upload-area {
  width: 100%;
  margin-bottom: 24px;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed #d0d5dd;
  border-radius: 16px;
  background: linear-gradient(135deg, #fafbfc 0%, #f0f4f8 100%);
  transition: all 0.3s ease;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8edff 100%);
}

.upload-area :deep(.el-icon--upload) {
  font-size: 56px;
  color: #667eea;
  margin-bottom: 12px;
}

.upload-area :deep(.el-upload__text) {
  font-size: 15px;
  color: #666;
}

.upload-area :deep(.el-upload__text em) {
  color: #667eea;
  font-weight: 500;
}

.upload-area :deep(.el-upload__tip) {
  margin-top: 12px;
  color: #999;
  font-size: 13px;
}

.selected-files {
  margin-top: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #eaeaea;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-weight: 600;
  color: #1a1a2e;
  font-size: 15px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid #eee;
  transition: all 0.2s ease;
}

.file-item:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.file-item .el-icon {
  color: #667eea;
  font-size: 18px;
}

.process-actions {
  margin-top: 24px;
  text-align: center;
}

.process-actions .el-button {
  min-width: 160px;
  border-radius: 10px;
  font-weight: 500;
}

.import-tabs {
  margin-bottom: 24px;
}

.import-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.import-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e0e0e0;
}

.import-tabs :deep(.el-tabs__item) {
  font-weight: 500;
  font-size: 15px;
  padding: 0 24px;
  height: 44px;
  line-height: 44px;
}

.import-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.import-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 批量生成律师函样式 */
.batch-lawyer-section {
  padding: 4px 0;
}

.batch-doc-type {
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #f0f4ff;
  border-radius: 12px;
  border: 1px solid #dce3f0;
}

.batch-upload-area {
  margin-bottom: 24px;
}

.batch-xlsx-upload :deep(.el-upload-dragger) {
  width: 100%;
  height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed #d0d5dd;
  border-radius: 16px;
  background: linear-gradient(135deg, #fafbfc 0%, #f0f4ff 100%);
  transition: all 0.3s ease;
}

.batch-xlsx-upload :deep(.el-upload-dragger:hover) {
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0fff4 0%, #e8ffe8 100%);
}

.batch-xlsx-upload :deep(.el-icon--upload) {
  font-size: 48px;
  color: #67c23a;
  margin-bottom: 8px;
}

.template-vars-hint {
  margin-bottom: 20px;
}

.var-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.var-tag-item {
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 12px;
}

.xlsx-preview {
  margin-top: 20px;
  padding: 20px;
  background: #fafbfc;
  border-radius: 12px;
  border: 1px solid #eaeaea;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  margin: 0;
  font-size: 16px;
  color: #1a1a2e;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.preview-header h4 .el-icon {
  color: #67c23a;
  font-size: 20px;
}

/* 表单美化 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #444;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #d0d5dd;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select__wrapper:hover) {
  border-color: #667eea;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-select__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

/* 按钮美化 */
:deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 表格美化 */
:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f8f9fa;
  font-weight: 600;
  color: #1a1a2e;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fafbfc;
}

/* 标签美化 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

/* 对话框美化 */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-bottom: 1px solid #eee;
  padding: 20px 24px;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  color: #1a1a2e;
}

/* 步骤指示器美化 */
:deep(.el-steps--simple) {
  background: transparent;
  padding: 12px 0;
}

:deep(.el-step__title) {
  font-weight: 500;
}

:deep(.el-step.is-success .el-step__title) {
  color: #67c23a;
}

:deep(.el-step.is-process .el-step__title) {
  color: #667eea;
}

:deep(.el-step__head.is-process) {
  color: #667eea;
  border-color: #667eea;
}

:deep(.el-step__head.is-success) {
  color: #67c23a;
  border-color: #67c23a;
}
</style>
