/**
 * 用户管理页面
 * ==============
 * 超级管理员管理系统用户
 *
 * 功能：
 * - 查看用户列表
 * - 按角色/状态筛选
 * - 搜索用户
 * - 添加/编辑用户
 * - 启用/禁用用户
 */

const app = getApp()

Page({
  data: {
    // 用户列表
    users: [],
    // 筛选条件
    filters: {
      role: '',      // 角色筛选
      status: '',    // 状态筛选
      keyword: ''    // 搜索关键词
    },
    // 角色选项
    roleOptions: [
      { value: '', label: '全部角色' },
      { value: 'resident', label: '居民' },
      { value: 'repairman', label: '维修人员' },
      { value: 'admin', label: '管理员' }
    ],
    // 状态选项
    statusOptions: [
      { value: '', label: '全部状态' },
      { value: 'active', label: '正常' },
      { value: 'disabled', label: '已禁用' }
    ],
    // 分页
    page: 1,
    hasMore: true,
    loading: false,
    // 弹窗控制
    showEditModal: false,
    editingUser: null,
    isNew: false,
    // 表单数据
    formData: {
      name: '',
      phone: '',
      role: 'resident'
    }
  },

  onLoad() {
    this.loadUsers()
  },

  /**
   * 加载用户列表
   */
  loadUsers(append = false) {
    if (this.data.loading) return

    this.setData({ loading: true })

    const { filters, page } = this.data
    let url = `/super/users?page=${page}&per_page=15`

    if (filters.role) url += `&role=${filters.role}`
    if (filters.status) url += `&status=${filters.status}`
    if (filters.keyword) url += `&keyword=${encodeURIComponent(filters.keyword)}`

    app.request({
      url: url,
      success: (res) => {
        if (res.data.code === 200) {
          const data = res.data.data
          // 处理用户数据，添加显示用的角色名称
          const users = data.items.map(user => ({
            ...user,
            roleName: this.getRoleName(user.role),
            statusName: user.status === 'active' ? '正常' : '已禁用'
          }))

          this.setData({
            users: append ? [...this.data.users, ...users] : users,
            hasMore: page < data.pages
          })
        }
      },
      complete: () => {
        this.setData({ loading: false })
      }
    })
  },

  /**
   * 获取角色显示名称
   */
  getRoleName(role) {
    const roleMap = {
      'resident': '居民',
      'repairman': '维修人员',
      'admin': '管理员',
      'super': '超级管理员'
    }
    return roleMap[role] || role
  },

  /**
   * 角色筛选变化
   */
  onRoleChange(e) {
    const roleIndex = e.detail.value
    this.setData({
      'filters.role': this.data.roleOptions[roleIndex].value,
      page: 1
    })
    this.loadUsers()
  },

  /**
   * 状态筛选变化
   */
  onStatusChange(e) {
    const statusIndex = e.detail.value
    this.setData({
      'filters.status': this.data.statusOptions[statusIndex].value,
      page: 1
    })
    this.loadUsers()
  },

  /**
   * 搜索关键词输入
   */
  onKeywordInput(e) {
    this.setData({
      'filters.keyword': e.detail.value
    })
  },

  /**
   * 执行搜索
   */
  doSearch() {
    this.setData({ page: 1 })
    this.loadUsers()
  },

  /**
   * 加载更多
   */
  loadMore() {
    if (!this.data.hasMore || this.data.loading) return

    this.setData({
      page: this.data.page + 1
    })
    this.loadUsers(true)
  },

  /**
   * 打开添加用户弹窗
   */
  showAddModal() {
    this.setData({
      showEditModal: true,
      isNew: true,
      editingUser: null,
      formData: {
        name: '',
        phone: '',
        role: 'resident'
      }
    })
  },

  /**
   * 打开编辑用户弹窗
   */
  editUser(e) {
    const user = e.currentTarget.dataset.user
    // 不能编辑超级管理员
    if (user.role === 'super') {
      wx.showToast({ title: '不能编辑超级管理员', icon: 'none' })
      return
    }

    this.setData({
      showEditModal: true,
      isNew: false,
      editingUser: user,
      formData: {
        name: user.name,
        phone: user.phone,
        role: user.role
      }
    })
  },

  /**
   * 关闭弹窗
   */
  closeModal() {
    this.setData({
      showEditModal: false,
      editingUser: null
    })
  },

  /**
   * 表单输入处理
   */
  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value })
  },

  onPhoneInput(e) {
    this.setData({ 'formData.phone': e.detail.value })
  },

  onRoleSelect(e) {
    const roles = ['resident', 'repairman', 'admin']
    this.setData({ 'formData.role': roles[e.detail.value] })
  },

  /**
   * 保存用户
   */
  saveUser() {
    const { formData, isNew, editingUser } = this.data

    // 验证表单
    if (!formData.name.trim()) {
      wx.showToast({ title: '请输入姓名', icon: 'none' })
      return
    }
    if (!formData.phone.trim()) {
      wx.showToast({ title: '请输入手机号', icon: 'none' })
      return
    }

    const url = isNew ? '/super/users' : `/super/users/${editingUser.id}`
    const method = isNew ? 'POST' : 'PUT'

    app.request({
      url: url,
      method: method,
      data: formData,
      success: (res) => {
        if (res.data.code === 200) {
          wx.showToast({ title: isNew ? '添加成功' : '修改成功', icon: 'success' })
          this.closeModal()
          this.setData({ page: 1 })
          this.loadUsers()
        } else {
          wx.showToast({ title: res.data.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  /**
   * 切换用户状态（启用/禁用）
   */
  toggleStatus(e) {
    const user = e.currentTarget.dataset.user

    // 不能禁用超级管理员
    if (user.role === 'super') {
      wx.showToast({ title: '不能禁用超级管理员', icon: 'none' })
      return
    }

    const newStatus = user.status === 'active' ? 'disabled' : 'active'
    const actionText = newStatus === 'active' ? '启用' : '禁用'

    wx.showModal({
      title: '确认操作',
      content: `确定要${actionText}用户"${user.name}"吗？`,
      success: (res) => {
        if (res.confirm) {
          app.request({
            url: `/super/users/${user.id}/status`,
            method: 'PUT',
            data: { status: newStatus },
            success: (res) => {
              if (res.data.code === 200) {
                wx.showToast({ title: `${actionText}成功`, icon: 'success' })
                this.loadUsers()
              } else {
                wx.showToast({ title: res.data.message || '操作失败', icon: 'none' })
              }
            }
          })
        }
      }
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.setData({ page: 1 })
    this.loadUsers()
    wx.stopPullDownRefresh()
  },

  /**
   * 上拉加载更多
   */
  onReachBottom() {
    this.loadMore()
  }
})
