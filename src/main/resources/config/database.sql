-- ============================================
-- 阳光社区报修系统 - 数据库初始化脚本
-- ============================================
-- 使用方法：
-- 1. 打开 MySQL 命令行或 Navicat 等工具
-- 2. 执行此脚本即可创建数据库和所有表
-- ============================================

-- 创建数据库（如果不存在）
-- UTF8MB4 支持中文和 emoji 表情
CREATE DATABASE IF NOT EXISTS community_repair
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 切换到该数据库
USE community_repair;

-- ============================================
-- 1. 用户表 (users)
-- 存储所有用户信息：居民、维修人员、管理员、超管
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，自动递增',
    openid VARCHAR(64) UNIQUE COMMENT '微信小程序唯一标识，用于微信登录',
    phone VARCHAR(20) COMMENT '手机号码',
    name VARCHAR(50) NOT NULL COMMENT '用户姓名',
    role ENUM('resident', 'repairman', 'admin', 'super') NOT NULL DEFAULT 'resident'
        COMMENT '用户角色：resident=居民, repairman=维修人员, admin=物业管理员, super=超级管理员',
    status ENUM('active', 'disabled') NOT NULL DEFAULT 'active'
        COMMENT '账号状态：active=正常, disabled=禁用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_role (role) COMMENT '角色索引，方便按角色查询用户',
    INDEX idx_phone (phone) COMMENT '手机号索引，方便按手机号查询'
) ENGINE=InnoDB COMMENT='用户表';

-- ============================================
-- 2. 楼栋表 (buildings)
-- 存储小区楼栋信息，用于报修时选择位置
-- ============================================
CREATE TABLE IF NOT EXISTS buildings (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '楼栋ID',
    name VARCHAR(50) NOT NULL COMMENT '楼栋名称，如"1栋"、"A座"',
    units INT NOT NULL DEFAULT 1 COMMENT '单元数量',
    floors INT NOT NULL DEFAULT 1 COMMENT '楼层数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB COMMENT='楼栋表';

-- ============================================
-- 3. 维修类别表 (repair_categories)
-- 存储维修类别，由管理员自定义配置
-- ============================================
CREATE TABLE IF NOT EXISTS repair_categories (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '类别ID',
    name VARCHAR(50) NOT NULL COMMENT '类别名称，如"水管维修"、"电路故障"',
    description VARCHAR(200) COMMENT '类别描述',
    status ENUM('active', 'disabled') NOT NULL DEFAULT 'active'
        COMMENT '状态：active=启用, disabled=禁用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_status (status) COMMENT '状态索引，方便查询启用的类别'
) ENGINE=InnoDB COMMENT='维修类别表';

-- ============================================
-- 4. 工单表 (work_orders)
-- 核心表！存储所有报修工单信息
-- ============================================
CREATE TABLE IF NOT EXISTS work_orders (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '工单ID',
    order_no VARCHAR(20) NOT NULL UNIQUE COMMENT '工单编号，如"WO202601110001"，方便用户查询',
    user_id INT NOT NULL COMMENT '报修居民ID',
    category_id INT NOT NULL COMMENT '维修类别ID',
    building_id INT COMMENT '楼栋ID，公共区域可为空',
    unit VARCHAR(10) COMMENT '单元号，如"1单元"',
    room VARCHAR(10) COMMENT '房号，如"101"',
    location_desc VARCHAR(200) COMMENT '位置描述，公共区域时使用，如"小区东门旁边"',
    description TEXT NOT NULL COMMENT '问题描述，居民填写的详细情况',
    contact_phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    status ENUM('pending', 'assigned', 'processing', 'completed', 'evaluated') NOT NULL DEFAULT 'pending'
        COMMENT '工单状态：pending=待审核, assigned=已分配, processing=处理中, completed=已完成, evaluated=已评价',
    assigned_to INT COMMENT '被分配的维修人员ID',
    assigned_at DATETIME COMMENT '分配时间',
    completed_at DATETIME COMMENT '完成时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间（报修时间）',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束：确保数据一致性
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES repair_categories(id) ON DELETE RESTRICT,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,

    -- 索引：加速常用查询
    INDEX idx_status (status) COMMENT '状态索引，方便按状态筛选工单',
    INDEX idx_user_id (user_id) COMMENT '用户索引，方便查询某个居民的所有工单',
    INDEX idx_assigned_to (assigned_to) COMMENT '维修人员索引，方便查询某个维修人员的工单',
    INDEX idx_created_at (created_at) COMMENT '创建时间索引，方便按时间排序'
) ENGINE=InnoDB COMMENT='工单表';

-- ============================================
-- 5. 工单图片表 (work_order_images)
-- 存储报修图片和维修完成图片
-- ============================================
CREATE TABLE IF NOT EXISTS work_order_images (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '图片ID',
    work_order_id INT NOT NULL COMMENT '所属工单ID',
    image_url VARCHAR(255) NOT NULL COMMENT '图片URL地址',
    type ENUM('report', 'repair') NOT NULL DEFAULT 'report'
        COMMENT '图片类型：report=报修时上传的图片, repair=维修完成后上传的图片',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',

    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
    INDEX idx_work_order_id (work_order_id) COMMENT '工单索引，方便查询某个工单的所有图片'
) ENGINE=InnoDB COMMENT='工单图片表';

-- ============================================
-- 6. 工单进度日志表 (work_order_logs)
-- 记录工单的每一次状态变更，形成完整的时间线
-- ============================================
CREATE TABLE IF NOT EXISTS work_order_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    work_order_id INT NOT NULL COMMENT '所属工单ID',
    operator_id INT NOT NULL COMMENT '操作人ID',
    action ENUM('create', 'audit', 'assign', 'start', 'complete', 'evaluate') NOT NULL
        COMMENT '操作类型：create=创建, audit=审核, assign=分配, start=开始处理, complete=完成, evaluate=评价',
    from_status VARCHAR(20) COMMENT '变更前状态',
    to_status VARCHAR(20) COMMENT '变更后状态',
    remark VARCHAR(500) COMMENT '备注说明，如维修人员的处理说明',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',

    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_work_order_id (work_order_id) COMMENT '工单索引，方便查询某个工单的所有日志'
) ENGINE=InnoDB COMMENT='工单进度日志表';

-- ============================================
-- 7. 评价表 (evaluations)
-- 存储居民对维修服务的评价
-- ============================================
CREATE TABLE IF NOT EXISTS evaluations (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '评价ID',
    work_order_id INT NOT NULL UNIQUE COMMENT '工单ID，一个工单只能有一条评价',
    user_id INT NOT NULL COMMENT '评价人ID（居民）',
    rating TINYINT NOT NULL COMMENT '评分，1-5星',
    content VARCHAR(500) COMMENT '评价内容，选填',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评价时间',

    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,

    -- 确保评分在1-5之间
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5)
) ENGINE=InnoDB COMMENT='评价表';

-- ============================================
-- 初始数据：创建超级管理员账号
-- ============================================
INSERT INTO users (name, phone, role, status) VALUES
    ('超级管理员', '13800000000', 'super', 'active');

-- ============================================
-- 初始数据：创建一些示例楼栋
-- ============================================
INSERT INTO buildings (name, units, floors) VALUES
    ('1栋', 2, 18),
    ('2栋', 2, 18),
    ('3栋', 3, 24);

-- ============================================
-- 初始数据：创建一些示例维修类别
-- ============================================
INSERT INTO repair_categories (name, description) VALUES
    ('水管维修', '水管漏水、堵塞、水龙头损坏等'),
    ('电路故障', '跳闸、插座损坏、灯具故障等'),
    ('门窗维修', '门锁损坏、玻璃破损、门窗变形等'),
    ('电梯故障', '电梯停运、异响、按钮失灵等'),
    ('公共设施', '健身器材、路灯、座椅等公共设施损坏');

-- ============================================
-- 完成提示
-- ============================================
SELECT '数据库初始化完成！' AS message;
SELECT '已创建超级管理员账号：13800000000' AS admin_info;
SELECT '已创建示例楼栋：1栋、2栋、3栋' AS building_info;
SELECT '已创建示例维修类别：水管维修、电路故障、门窗维修、电梯故障、公共设施' AS category_info;
