/**
 * 楼栋管理页面
 * ==============
 * 超级管理员管理小区楼栋信息
 *
 * 功能：
 * - 查看楼栋列表
 * - 添加新楼栋
 * - 编辑楼栋信息
 * - 删除楼栋（无工单时才可删除）
 */

const app = getApp()

Page({
  data: {
    // 楼栋列表
    buildings: [],
    loading: false,
    // 弹窗控制
    showEditModal: false,
    editingBuilding: null,
    isNew: false,
    // 表单数据
    formData: {
      name: '',
      units: 1,
      floors: 1
    }
  },

  onLoad() {
    this.loadBuildings()
  },

  /**
   * 加载楼栋列表
   */
  loadBuildings() {
    this.setData({ loading: true })

    app.request({
      url: '/buildings',
      success: (res) => {
        if (res.data.code === 200) {
          this.setData({
            buildings: res.data.data
          })
        }
      },
      complete: () => {
        this.setData({ loading: false })
      }
    })
  },

  /**
   * 打开添加楼栋弹窗
   */
  showAddModal() {
    this.setData({
      showEditModal: true,
      isNew: true,
      editingBuilding: null,
      formData: {
        name: '',
        units: 1,
        floors: 1
      }
    })
  },

  /**
   * 打开编辑楼栋弹窗
   */
  editBuilding(e) {
    const building = e.currentTarget.dataset.building
    this.setData({
      showEditModal: true,
      isNew: false,
      editingBuilding: building,
      formData: {
        name: building.name,
        units: building.units,
        floors: building.floors
      }
    })
  },

  /**
   * 关闭弹窗
   */
  closeModal() {
    this.setData({
      showEditModal: false,
      editingBuilding: null
    })
  },

  /**
   * 表单输入处理
   */
  onNameInput(e) {
    this.setData({ 'formData.name': e.detail.value })
  },

  onUnitsInput(e) {
    const value = parseInt(e.detail.value) || 1
    this.setData({ 'formData.units': value })
  },

  onFloorsInput(e) {
    const value = parseInt(e.detail.value) || 1
    this.setData({ 'formData.floors': value })
  },

  /**
   * 保存楼栋
   */
  saveBuilding() {
    const { formData, isNew, editingBuilding } = this.data

    // 验证表单
    if (!formData.name.trim()) {
      wx.showToast({ title: '请输入楼栋名称', icon: 'none' })
      return
    }

    const url = isNew ? '/super/buildings' : `/super/buildings/${editingBuilding.id}`
    const method = isNew ? 'POST' : 'PUT'

    app.request({
      url: url,
      method: method,
      data: {
        name: formData.name,
        units: formData.units,
        floors: formData.floors
      },
      success: (res) => {
        if (res.data.code === 200) {
          wx.showToast({ title: isNew ? '添加成功' : '修改成功', icon: 'success' })
          this.closeModal()
          this.loadBuildings()
        } else {
          wx.showToast({ title: res.data.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  /**
   * 删除楼栋
   */
  deleteBuilding(e) {
    const building = e.currentTarget.dataset.building

    wx.showModal({
      title: '确认删除',
      content: `确定要删除"${building.name}"吗？\n注意：如果该楼栋下有工单，将无法删除。`,
      confirmColor: '#ff4d4f',
      success: (res) => {
        if (res.confirm) {
          app.request({
            url: `/super/buildings/${building.id}`,
            method: 'DELETE',
            success: (res) => {
              if (res.data.code === 200) {
                wx.showToast({ title: '删除成功', icon: 'success' })
                this.loadBuildings()
              } else {
                wx.showToast({ title: res.data.message || '删除失败', icon: 'none' })
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
    this.loadBuildings()
    wx.stopPullDownRefresh()
  }
})
