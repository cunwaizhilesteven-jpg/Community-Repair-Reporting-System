/**
 * 报修页面
 * ========
 * 居民提交报修申请的页面。
 *
 * 功能：
 * 1. 选择维修类别
 * 2. 选择报修位置（楼栋/单元/房号）
 * 3. 填写问题描述
 * 4. 上传图片
 * 5. 提交报修
 */

const app = getApp();

Page({
  data: {
    // 表单数据
    categoryId: null,       // 选中的类别ID
    buildingId: null,       // 选中的楼栋ID
    unit: '',               // 单元号
    room: '',               // 房号
    locationDesc: '',       // 位置描述（公共区域）
    description: '',        // 问题描述
    contactPhone: '',       // 联系电话
    images: [],             // 上传的图片列表

    // 选项数据
    categories: [],         // 维修类别列表
    buildings: [],          // 楼栋列表

    // 选择器索引
    categoryIndex: -1,
    buildingIndex: -1,

    // 状态
    isPublicArea: false,    // 是否是公共区域
    submitting: false       // 是否正在提交
  },

  onLoad() {
    this.loadData();
  },

  /**
   * 加载基础数据
   */
  loadData() {
    // 并行加载类别和楼栋数据
    Promise.all([
      app.request({ url: '/categories' }),
      app.request({ url: '/buildings' })
    ]).then(([categoriesRes, buildingsRes]) => {
      const userPhone = app.globalData.userInfo?.phone || '';

      this.setData({
        categories: categoriesRes.data,
        buildings: buildingsRes.data,
        contactPhone: userPhone
      });
    });
  },

  /**
   * 选择维修类别
   */
  onCategoryChange(e) {
    const index = e.detail.value;
    this.setData({
      categoryIndex: index,
      categoryId: this.data.categories[index].id
    });
  },

  /**
   * 选择楼栋
   */
  onBuildingChange(e) {
    const index = e.detail.value;
    this.setData({
      buildingIndex: index,
      buildingId: this.data.buildings[index].id
    });
  },

  /**
   * 切换公共区域
   */
  onPublicAreaChange(e) {
    this.setData({
      isPublicArea: e.detail.value,
      // 切换时清空相关字段
      buildingId: null,
      buildingIndex: -1,
      unit: '',
      room: '',
      locationDesc: ''
    });
  },

  /**
   * 输入单元号
   */
  onUnitInput(e) {
    this.setData({ unit: e.detail.value });
  },

  /**
   * 输入房号
   */
  onRoomInput(e) {
    this.setData({ room: e.detail.value });
  },

  /**
   * 输入位置描述
   */
  onLocationDescInput(e) {
    this.setData({ locationDesc: e.detail.value });
  },

  /**
   * 输入问题描述
   */
  onDescriptionInput(e) {
    this.setData({ description: e.detail.value });
  },

  /**
   * 输入联系电话
   */
  onPhoneInput(e) {
    this.setData({ contactPhone: e.detail.value });
  },

  /**
   * 选择图片
   */
  chooseImage() {
    const maxCount = 3 - this.data.images.length;

    if (maxCount <= 0) {
      wx.showToast({ title: '最多上传3张图片', icon: 'none' });
      return;
    }

    wx.chooseMedia({
      count: maxCount,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        // 上传每张图片
        res.tempFiles.forEach((file) => {
          this.uploadImage(file.tempFilePath);
        });
      }
    });
  },

  /**
   * 上传单张图片
   */
  uploadImage(filePath) {
    wx.showLoading({ title: '上传中...' });

    wx.uploadFile({
      url: app.globalData.baseUrl + '/upload/image',
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success: (res) => {
        const data = JSON.parse(res.data);
        if (data.code === 200) {
          this.setData({
            images: [...this.data.images, data.data.url]
          });
        } else {
          wx.showToast({ title: data.message || '上传失败', icon: 'none' });
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' });
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },

  /**
   * 删除图片
   */
  deleteImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = this.data.images;
    images.splice(index, 1);
    this.setData({ images });
  },

  /**
   * 预览图片
   */
  previewImage(e) {
    const url = e.currentTarget.dataset.url;
    wx.previewImage({
      urls: this.data.images,
      current: url
    });
  },

  /**
   * 提交报修
   */
  submitOrder() {
    // 表单验证
    if (!this.data.categoryId) {
      wx.showToast({ title: '请选择维修类别', icon: 'none' });
      return;
    }

    if (!this.data.isPublicArea && !this.data.buildingId) {
      wx.showToast({ title: '请选择楼栋', icon: 'none' });
      return;
    }

    if (this.data.isPublicArea && !this.data.locationDesc) {
      wx.showToast({ title: '请填写位置描述', icon: 'none' });
      return;
    }

    if (!this.data.description) {
      wx.showToast({ title: '请填写问题描述', icon: 'none' });
      return;
    }

    if (!this.data.contactPhone) {
      wx.showToast({ title: '请填写联系电话', icon: 'none' });
      return;
    }

    // 构建请求数据
    const data = {
      category_id: this.data.categoryId,
      description: this.data.description,
      contact_phone: this.data.contactPhone,
      images: this.data.images
    };

    if (this.data.isPublicArea) {
      data.location_desc = this.data.locationDesc;
    } else {
      data.building_id = this.data.buildingId;
      data.unit = this.data.unit;
      data.room = this.data.room;
    }

    // 提交
    this.setData({ submitting: true });

    app.request({
      url: '/work-orders',
      method: 'POST',
      data
    }).then((res) => {
      wx.showToast({ title: '提交成功', icon: 'success' });

      // 返回上一页
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).finally(() => {
      this.setData({ submitting: false });
    });
  }
});
