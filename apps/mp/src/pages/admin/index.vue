<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw Admin</text>
      <view style="height: 18rpx" />
      <text class="title">这里是内容审核台，用来处理帖子、评论和后续扩展的安全问题。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">管理员可以在这里查看举报统计、筛选举报记录，并直接执行结案、驳回、删除或关闭违规内容。</text>
    </view>

    <view v-if="!isAdmin" class="card empty section">
      <text class="section-title">当前账号没有后台权限</text>
      <view style="height: 12rpx" />
      <text class="section-desc">只有管理员账号才能进入内容审核台。你可以先回到论坛继续查看前台页面。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-ghost" @tap="goForum">返回论坛首页</button>
    </view>

    <view v-else class="section">
      <view class="grid stats-grid section">
        <view class="card stat-card">
          <text class="helper">全部举报</text>
          <view style="height: 8rpx" />
          <text class="stat-value">{{ stats.all }}</text>
        </view>
        <view class="card stat-card">
          <text class="helper">待处理</text>
          <view style="height: 8rpx" />
          <text class="stat-value">{{ stats.open }}</text>
        </view>
        <view class="card stat-card">
          <text class="helper">处理中</text>
          <view style="height: 8rpx" />
          <text class="stat-value">{{ stats.reviewing }}</text>
        </view>
        <view class="card stat-card">
          <text class="helper">已解决</text>
          <view style="height: 8rpx" />
          <text class="stat-value">{{ stats.resolved }}</text>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">举报列表</text>
            <view style="height: 8rpx" />
            <text class="section-desc">当前支持论坛帖子、评论和交易帖子的基础审核处理。</text>
          </view>
          <button class="btn btn-ghost" :disabled="loading" @tap="loadData">
            {{ loading ? '刷新中...' : '刷新' }}
          </button>
        </view>

        <view style="height: 20rpx" />

        <view class="filter-group">
          <text class="helper">按状态筛选</text>
          <view style="height: 12rpx" />
          <view class="filter-row">
            <button
              v-for="item in statusFilters"
              :key="item.value"
              class="btn btn-ghost filter-btn"
              :class="{ active: currentStatus === item.value }"
              @tap="changeStatus(item.value)"
            >
              {{ item.label }}
            </button>
          </view>
        </view>

        <view style="height: 16rpx" />

        <view class="filter-group">
          <text class="helper">按内容类型筛选</text>
          <view style="height: 12rpx" />
          <view class="filter-row">
            <button
              v-for="item in typeFilters"
              :key="item.value"
              class="btn btn-ghost filter-btn"
              :class="{ active: currentTargetType === item.value }"
              @tap="changeTargetType(item.value)"
            >
              {{ item.label }}
            </button>
          </view>
        </view>

        <view style="height: 20rpx" />

        <view v-if="reports.length" class="grid">
          <view v-for="report in reports" :key="report.id" class="card report-card">
            <view class="report-head">
              <view style="flex: 1">
                <text class="section-title report-title">{{ report.target_snapshot.label }}</text>
                <view style="height: 8rpx" />
                <text class="helper">{{ getReportMeta(report) }}</text>
              </view>
              <text class="status-badge" :class="`status-${report.status}`">{{ getStatusLabel(report.status) }}</text>
            </view>

            <view style="height: 14rpx" />
            <text class="section-desc">举报原因：{{ report.reason }}</text>
            <view v-if="report.details" style="height: 10rpx" />
            <text v-if="report.details" class="helper">补充说明：{{ report.details }}</text>
            <view style="height: 10rpx" />
            <text class="helper">内容类型：{{ getTargetTypeLabel(report.target_type) }} · 创建时间：{{ formatDate(report.created_at) }}</text>

            <view style="height: 18rpx" />
            <view class="action-row">
              <button
                class="btn btn-ghost"
                :disabled="submittingId === report.id"
                @tap="reviewReport(report.id, 'reviewing')"
              >
                设为处理中
              </button>
              <button
                class="btn btn-primary"
                :disabled="submittingId === report.id"
                @tap="reviewReport(report.id, 'resolved')"
              >
                标记解决
              </button>
              <button
                class="btn btn-ghost"
                :disabled="submittingId === report.id"
                @tap="reviewReport(report.id, 'rejected')"
              >
                驳回举报
              </button>
              <button
                v-if="report.target_type === 'forum_post'"
                class="btn btn-secondary"
                :disabled="submittingId === report.id || report.target_snapshot.is_deleted"
                @tap="deleteForumPost(report.id)"
              >
                {{ report.target_snapshot.is_deleted ? '帖子已删除' : '删除帖子并结案' }}
              </button>
              <button
                v-if="report.target_type === 'comment'"
                class="btn btn-secondary"
                :disabled="submittingId === report.id"
                @tap="deleteForumComment(report.id)"
              >
                删除评论并结案
              </button>
              <button
                v-if="report.target_type === 'trade_post'"
                class="btn btn-secondary"
                :disabled="submittingId === report.id || report.target_snapshot.status === 'closed'"
                @tap="closeTradePost(report.id)"
              >
                {{ report.target_snapshot.status === 'closed' ? '交易已关闭' : '关闭交易并结案' }}
              </button>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-title" style="font-size: 32rpx">当前筛选条件下没有举报记录</text>
          <view style="height: 10rpx" />
          <text class="section-desc">这说明当前内容比较干净，或者还没有人发起新的举报。</text>
        </view>
      </view>

      <view class="card">
        <text class="section-title">最近审核操作</text>
        <view style="height: 12rpx" />
        <view v-if="actionLogs.length" class="log-list">
          <view v-for="log in actionLogs" :key="log.id" class="log-item">
            <text class="log-title">{{ getActionLabel(log.action) }}</text>
            <view style="height: 6rpx" />
            <text class="helper">{{ log.note || getTargetTypeLabel(log.target_type) }} · {{ formatDate(log.created_at) }}</text>
          </view>
        </view>
        <text v-else class="section-desc">暂无审核操作记录。</text>
      </view>

      <view class="card">
        <text class="section-title">Django Admin 入口</text>
        <view style="height: 12rpx" />
        <text class="section-desc">如果你还需要更完整的后台管理能力，也可以继续进入 Django Admin。</text>
        <view style="height: 16rpx" />
        <text selectable class="url-text">{{ adminUrl }}</text>
        <view style="height: 18rpx" />
        <button class="btn btn-ghost" @tap="copyUrl">复制后台地址</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import type { ModerationActionLog, ModerationReport, ModerationReportStats } from '../../types/api'
import {
  fetchModerationActionLogs,
  fetchModerationReports,
  fetchModerationReportStats,
  reviewModerationReport,
} from '../../services/moderation'
import { currentUser, ensureAuthenticated } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { getAdminUrl } from '../../utils/request'
import { showToast } from '../../utils/ui'

const adminUrl = getAdminUrl()
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentStatus = ref('')
const currentTargetType = ref('')
const loading = ref(false)
const submittingId = ref('')
const reports = ref<ModerationReport[]>([])
const actionLogs = ref<ModerationActionLog[]>([])
const stats = reactive<ModerationReportStats>({
  all: 0,
  open: 0,
  reviewing: 0,
  resolved: 0,
  rejected: 0,
})

const statusFilters = [
  { label: '全部状态', value: '' },
  { label: '待处理', value: 'open' },
  { label: '处理中', value: 'reviewing' },
  { label: '已解决', value: 'resolved' },
  { label: '已驳回', value: 'rejected' },
]

const typeFilters = [
  { label: '全部类型', value: '' },
  { label: '帖子举报', value: 'forum_post' },
  { label: '评论举报', value: 'comment' },
  { label: '交易举报', value: 'trade_post' },
]

async function loadData() {
  if (!isAdmin.value) {
    return
  }

  loading.value = true
  try {
    const [statsData, reportsData, logsData] = await Promise.all([
      fetchModerationReportStats(),
      fetchModerationReports({
        status: currentStatus.value || undefined,
        target_type: currentTargetType.value || undefined,
      }),
      fetchModerationActionLogs(),
    ])
    Object.assign(stats, statsData)
    reports.value = reportsData
    actionLogs.value = logsData
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载审核数据失败')
  } finally {
    loading.value = false
  }
}

function changeStatus(status: string) {
  currentStatus.value = status
  loadData()
}

function changeTargetType(targetType: string) {
  currentTargetType.value = targetType
  loadData()
}

async function reviewReport(reportId: string, status: ModerationReport['status']) {
  submittingId.value = reportId
  try {
    await reviewModerationReport(reportId, { status, action: 'none' })
    showToast('处理结果已保存', 'success')
    await loadData()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '处理举报失败')
  } finally {
    submittingId.value = ''
  }
}

async function deleteForumPost(reportId: string) {
  submittingId.value = reportId
  try {
    await reviewModerationReport(reportId, {
      status: 'resolved',
      action: 'delete_forum_post',
    })
    showToast('帖子已删除并结案', 'success')
    await loadData()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '删除帖子失败')
  } finally {
    submittingId.value = ''
  }
}

async function deleteForumComment(reportId: string) {
  submittingId.value = reportId
  try {
    await reviewModerationReport(reportId, {
      status: 'resolved',
      action: 'delete_forum_comment',
    })
    showToast('评论已删除并结案', 'success')
    await loadData()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '删除评论失败')
  } finally {
    submittingId.value = ''
  }
}

async function closeTradePost(reportId: string) {
  submittingId.value = reportId
  try {
    await reviewModerationReport(reportId, {
      status: 'resolved',
      action: 'close_trade_post',
    })
    showToast('交易已关闭并结案', 'success')
    await loadData()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '关闭交易失败')
  } finally {
    submittingId.value = ''
  }
}

function getStatusLabel(status: ModerationReport['status']) {
  if (status === 'open') {
    return '待处理'
  }
  if (status === 'reviewing') {
    return '处理中'
  }
  if (status === 'resolved') {
    return '已解决'
  }
  return '已驳回'
}

function getTargetTypeLabel(targetType: string) {
  if (targetType === 'forum_post') {
    return '论坛帖子'
  }
  if (targetType === 'comment') {
    return '论坛评论'
  }
  if (targetType === 'trade_post') {
    return '交易帖子'
  }
  if (targetType === 'dating_profile') {
    return '匹配资料'
  }
  if (targetType === 'team_post') {
    return '组队帖子'
  }
  if (targetType === 'user') {
    return '用户'
  }
  return targetType
}

function getActionLabel(action: string) {
  const map: Record<string, string> = {
    delete_forum_post: '删除论坛帖子',
    delete_forum_comment: '删除论坛评论',
    close_trade_post: '关闭交易帖子',
    set_status_open: '重开举报',
    set_status_reviewing: '设为处理中',
    set_status_resolved: '标记解决',
    set_status_rejected: '驳回举报',
  }
  return map[action] || action
}

function getReportMeta(report: ModerationReport) {
  const reporter = report.reporter.nickname || report.reporter.full_name || report.reporter.email
  return `举报人：${reporter}`
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

function copyUrl() {
  uni.setClipboardData({
    data: adminUrl,
    success: () => showToast('后台地址已复制', 'success'),
  })
}

function goForum() {
  navigateTo('/pages/forum/index')
}

onShow(() => {
  if (!ensureAuthenticated('/pages/admin/index')) {
    return
  }
  if (isAdmin.value) {
    loadData()
  }
})
</script>

<style scoped lang="scss">
.hero {
  padding-top: 12rpx;
}

.stats-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stat-card {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 44rpx;
  font-weight: 700;
  color: #102133;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.filter-btn.active {
  background: rgba(241, 107, 79, 0.14);
  color: #f16b4f;
}

.report-card {
  display: flex;
  flex-direction: column;
}

.report-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.report-title {
  margin-bottom: 0;
  font-size: 30rpx;
}

.status-badge {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.status-open {
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
}

.status-reviewing {
  background: rgba(255, 193, 7, 0.18);
  color: #9a6700;
}

.status-resolved {
  background: rgba(77, 166, 106, 0.18);
  color: #2e7d49;
}

.status-rejected {
  background: rgba(16, 33, 51, 0.1);
  color: #4b5563;
}

.action-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.url-text {
  display: block;
  padding: 20rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 250, 245, 0.92);
  border: 1rpx solid rgba(16, 33, 51, 0.12);
  font-size: 24rpx;
  line-height: 1.7;
  color: #102133;
  word-break: break-all;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.log-item {
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 250, 245, 0.92);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.log-title {
  color: #102133;
  font-size: 27rpx;
  font-weight: 800;
}
</style>
