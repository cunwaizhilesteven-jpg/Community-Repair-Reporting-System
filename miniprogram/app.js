/**
 * 小程序入口文件
 * ================
 * 这是小程序的"总管"，负责：
 * 1. 初始化全局数据
 * 2. 处理用户登录
 * 3. 提供全局方法
 */

App({
  /**
   * 全局数据
   * 所有页面都可以通过 getApp().globalData 访问
   */
  globalData: {
    // 后端 API 地址
    // 开发时使用本地地址，上线时改成正式服务器地址
    baseUrl: 'http://localhost:5000/api/v1',

    // 用户信息
    userInfo: null,

    // 登录 Token
    token: null,

    // 是否已登录
    isLoggedIn: false,

    // ========================================
    // 开发模式配置
    // ========================================
    // 设置为 true 启用模拟登录（不需要真实微信登录）
    devMode: true,

    // 开发模式下模拟的用户 openid
    // 可以切换不同角色测试：
    // 'resident1_test_openid'  - 居民（赵居民）
    // 'resident2_test_openid'  - 居民（钱居民）
    // 'repair1_test_openid'    - 维修人员（李师傅）
    // 'repair2_test_openid'    - 维修人员（王师傅）
    // 'admin_test_openid'      - 管理员（张管理）
    // 'super_test_openid'      - 超级管理员
    devOpenid: 'resident1_test_openid'
  },

  /**
   * 小程序启动时执行
   */
  onLaunch() {
    console.log('小程序启动');

    // 尝试从本地存储恢复登录状态
    this.checkLoginStatus();

    // 预加载微信通知模板ID
    this.loadNotifyTemplates();
  },

  /**
   * 预加载微信通知模板ID
   * 在启动时获取模板ID并缓存，后续点击订阅时直接使用，
   * 避免异步请求导致手势上下文丢失。
   */
  loadNotifyTemplates() {
    this.request({
      url: '/notify/templates',
      noAuth: true
    }).then(res => {
      const templates = res.data && res.data.templates;
      if (templates && templates.length > 0) {
        this.globalData.notifyTemplates = templates;
        console.log('[微信通知] 模板ID加载成功:', templates);
      }
    }).catch(() => {});
  },

  /**
   * 检查登录状态
   * 从本地存储读取之前保存的 Token
   */
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');

    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      this.globalData.isLoggedIn = true;
      console.log('已恢复登录状态');
    }
  },

  /**
   * 用户登录
   * @returns {Promise} 登录结果
   */
  login() {
    return new Promise((resolve, reject) => {
      // ========================================
      // 开发模式：使用模拟登录
      // ========================================
      if (this.globalData.devMode) {
        console.log('开发模式：使用模拟登录');
        this.request({
          url: '/auth/dev-login',
          method: 'POST',
          data: { openid: this.globalData.devOpenid },
          noAuth: true
        }).then((result) => {
          // 保存登录信息
          this.globalData.token = result.data.token;
          this.globalData.userInfo = result.data.user;
          this.globalData.isLoggedIn = true;

          wx.setStorageSync('token', result.data.token);
          wx.setStorageSync('userInfo', result.data.user);

          console.log('登录成功:', result.data.user);
          resolve(result.data);
        }).catch(reject);
        return;
      }

      // ========================================
      // 正式模式：使用微信登录
      // ========================================
      wx.login({
        success: (res) => {
          if (res.code) {
            // 将 code 发送到后端换取 Token
            this.request({
              url: '/auth/login',
              method: 'POST',
              data: { code: res.code },
              noAuth: true  // 登录接口不需要 Token
            }).then((result) => {
              // 保存登录信息
              this.globalData.token = result.data.token;
              this.globalData.userInfo = result.data.user;
              this.globalData.isLoggedIn = true;

              // 保存到本地存储（下次打开小程序可以恢复）
              wx.setStorageSync('token', result.data.token);
              wx.setStorageSync('userInfo', result.data.user);

              resolve(result.data);
            }).catch(reject);
          } else {
            reject(new Error('微信登录失败'));
          }
        },
        fail: reject
      });
    });
  },

  /**
   * 退出登录
   */
  logout() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.isLoggedIn = false;

    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
  },

  /**
   * 封装的网络请求方法
   * 自动添加 Token、处理错误
   *
   * @param {Object} options 请求选项
   * @param {string} options.url - 接口路径（不含 baseUrl）
   * @param {string} options.method - 请求方法，默认 GET
   * @param {Object} options.data - 请求数据
   * @param {boolean} options.noAuth - 是否不需要认证
   * @returns {Promise} 请求结果
   */
  request(options) {
    return new Promise((resolve, reject) => {
      const { url, method = 'GET', data, noAuth = false } = options;

      // 构建请求头
      const header = {
        'Content-Type': 'application/json'
      };

      // 如果需要认证，添加 Token
      if (!noAuth && this.globalData.token) {
        header['Authorization'] = `Bearer ${this.globalData.token}`;
      }

      // 发送请求
      wx.request({
        url: this.globalData.baseUrl + url,
        method,
        data,
        header,
        success: (res) => {
          if (res.statusCode === 200) {
            if (res.data.code === 200) {
              resolve(res.data);
            } else {
              // 业务错误
              wx.showToast({
                title: res.data.message || '请求失败',
                icon: 'none'
              });
              reject(res.data);
            }
          } else if (res.statusCode === 401) {
            // 未登录或 Token 过期
            this.logout();
            wx.showToast({
              title: '请重新登录',
              icon: 'none'
            });
            reject(new Error('未登录'));
          } else {
            // 其他错误
            wx.showToast({
              title: res.data.message || '网络错误',
              icon: 'none'
            });
            reject(res.data);
          }
        },
        fail: (err) => {
          wx.showToast({
            title: '网络连接失败',
            icon: 'none'
          });
          reject(err);
        }
      });
    });
  },

  /**
   * 请求微信订阅消息授权
   * 获取后端已配置的模板ID，向用户发起订阅请求。
   * 用户同意后，工单状态变更时会收到微信通知。
   */
  subscribeMessages() {
    if (!this.globalData.isLoggedIn) return;

    // 使用已缓存的模板ID（启动时预加载）
    // 直接同步调用 wx.requestSubscribeMessage，保留用户手势上下文
    const tmplIds = this.globalData.notifyTemplates || [];
    if (tmplIds.length === 0) {
      console.log('[微信通知] 未加载到模板ID，请确认后端已配置');
      return;
    }

    wx.requestSubscribeMessage({
      tmplIds: tmplIds,
      success: (subRes) => {
        console.log('[微信通知] 订阅结果:', subRes);
      },
      fail: (err) => {
        console.log('[微信通知] 订阅失败:', err);
      }
    });
  },
});
