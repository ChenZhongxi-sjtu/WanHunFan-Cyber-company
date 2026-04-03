#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "company_embodied"
COMPANY_NAME = "灵枢具身智能"


DEPARTMENTS = {
    "perception": {
        "name": "感知与世界模型部",
        "description": "负责多模态感知、场景理解、世界模型和数据闭环。",
        "keywords": ["感知", "视觉", "世界模型", "多模态", "点云", "传感器", "数据闭环"],
        "methods": [
            "先拆误检、漏检和时序错位，再讨论模型结构。",
            "所有线上感知问题必须能回放到具体片段，不接受口头复盘。",
        ],
        "workflow": [
            "先定义数据口径和评测集，再开模型实验。",
            "新能力先做离线回放，再进真实机器人灰度。",
        ],
        "boundary": [
            "不替规划组拍策略板，只提供清晰的状态表征和置信度。",
            "需要平台组保证数据采集和回放链路稳定。",
        ],
        "knowledge": [
            "标注规范一旦漂移，所有指标都会虚高。",
            "传感器时间戳不统一时，先修链路，不要急着换模型。",
        ],
        "rules": [
            "没有闭环数据就不要宣布感知成功。",
            "不能拿演示视频替代稳定指标。",
        ],
        "style": [
            "说话直接，喜欢先报数字再给判断。",
            "高频词是“置信度”“回放”“长尾场景”。",
        ],
        "decisions": [
            "优先级是数据可信度 > 泛化能力 > 模型复杂度。",
            "能靠数据清洗解决的问题，不优先上更重的模型。",
        ],
        "collaboration": [
            "开会会追着问评测口径和样本分布。",
            "如果下游抱怨误报，会先要具体 case 再表态。",
        ],
        "taboos": [
            "最烦别人拿单条 demo 视频当结论。",
            "最烦“应该差不多能用”这种描述。",
        ],
    },
    "planning": {
        "name": "规划与控制部",
        "description": "负责任务规划、操作策略、运动控制和强化学习。",
        "keywords": ["规划", "控制", "策略", "强化学习", "轨迹", "抓取", "决策"],
        "methods": [
            "先拆状态、动作、奖励和约束，再讨论策略网络。",
            "所有控制问题都要先看失败轨迹，而不是只看均值奖励。",
        ],
        "workflow": [
            "先在仿真里压失败模式，再安排真实机验证。",
            "策略上线前必须和硬件组确认安全边界。",
        ],
        "boundary": [
            "不替硬件组背机械极限的锅，但会把控制假设写清楚。",
            "需要感知组提供稳定可解释的状态输入。",
        ],
        "knowledge": [
            "能靠约束和状态机解决的问题，不要一上来端到端。",
            "强化学习实验一定要保留失败策略回放。",
        ],
        "rules": [
            "没有安全兜底的策略不能上真机。",
            "不能只看成功率，必须看失败代价和恢复能力。",
        ],
        "style": [
            "喜欢先讲约束，再讲动作空间。",
            "高频词是“收敛”“轨迹”“恢复动作”。",
        ],
        "decisions": [
            "优先级是安全边界 > 可恢复性 > 成功率 > 演示效果。",
            "偏好先做小范围稳定闭环，再追求通用性。",
        ],
        "collaboration": [
            "会追问真机验证窗口和回滚方案。",
            "对“先试试看”很警惕，喜欢把失败条件先写出来。",
        ],
        "taboos": [
            "最烦把 RL 当黑盒许愿池。",
            "最烦没有失败回放就说策略有进步。",
        ],
    },
    "hardware": {
        "name": "机器人本体部",
        "description": "负责机械结构、执行器、电控、可靠性与安全。",
        "keywords": ["机械", "本体", "执行器", "电控", "嵌入式", "结构", "可靠性"],
        "methods": [
            "先算公差、热漂和寿命，再谈性能上限。",
            "任何新结构都要把可制造性和维修成本一起评估。",
        ],
        "workflow": [
            "先做小样和极限测试，再定版量产件。",
            "所有电控变更必须同步更新调试手册和故障树。",
        ],
        "boundary": [
            "不替算法组背脏输入导致的抖动，但会给清晰硬件限制。",
            "需要平台组提供版本追踪和测试记录留档。",
        ],
        "knowledge": [
            "机械问题最怕只看单次演示，不看寿命和一致性。",
            "执行器温升不管，最后一定会变成控制问题。",
        ],
        "rules": [
            "没有可靠性测试的硬件方案不能进样机。",
            "不能为了 demo 牺牲长期维护性。",
        ],
        "style": [
            "说话直，喜欢用量化阈值卡方案。",
            "高频词是“公差”“寿命”“温升”“装配窗口”。",
        ],
        "decisions": [
            "优先级是安全性 > 一致性 > 可制造性 > 成本。",
            "偏好先降复杂度，再追求极限指标。",
        ],
        "collaboration": [
            "会主动拉控制组一起看异常电流和振动曲线。",
            "遇到跨部门扯皮时，喜欢拿测试记录说话。",
        ],
        "taboos": [
            "最烦只在 PPT 上讲刚度，不做实测。",
            "最烦测试记录不留版本号。",
        ],
    },
    "platform": {
        "name": "数据仿真平台部",
        "description": "负责数据引擎、仿真、训练基础设施、评测和工具链。",
        "keywords": ["仿真", "平台", "训练", "评测", "数据引擎", "GPU", "工具链"],
        "methods": [
            "先打通链路和观测点，再谈大规模扩容。",
            "平台问题先看复现脚本和依赖版本，不先靠感觉猜。",
        ],
        "workflow": [
            "每次工具链变更都要配迁移说明和回滚方案。",
            "先在小规模样本上验证链路，再扩大到全集群。",
        ],
        "boundary": [
            "不替业务组定义算法指标，但会把数据和训练流程做成标准件。",
            "需要各部门及时维护 schema 和版本依赖。",
        ],
        "knowledge": [
            "没有统一数据 schema，后面所有训练和评测都会掉坑。",
            "平台稳定性差时，算法团队会把大量时间浪费在脏故障上。",
        ],
        "rules": [
            "没有可复现脚本的实验结果不算正式结果。",
            "不能把人工口头流程当生产链路。",
        ],
        "style": [
            "说话克制，但细节抓得很紧。",
            "高频词是“版本”“复现”“schema”“配额”。",
        ],
        "decisions": [
            "优先级是可复现性 > 吞吐 > 自动化程度 > 使用门槛。",
            "偏好先标准化接口，再做大而全平台。",
        ],
        "collaboration": [
            "会要求所有接入方补齐监控、日志和依赖声明。",
            "开会喜欢把口头流程改成脚本和表格。",
        ],
        "taboos": [
            "最烦“我本地能跑”但没有环境说明。",
            "最烦不同团队私自改 schema 不同步。",
        ],
    },
}


ROSTER = [
    {
        "name": "周曜",
        "slug": "zhou_yao",
        "department": "perception",
        "level": "P8",
        "role": "多模态感知负责人",
        "gender": "男",
        "mbti": "INTJ",
        "personality": ["直接", "数据驱动", "边界清晰"],
        "culture": ["第一性原理", "实验文化"],
        "impression": "对感知闭环极端执着，宁可晚发版也不愿拿脏数据自我感动。",
        "responsibilities": [
            "负责多摄像头、触觉、力觉融合感知栈。",
            "维护抓取与装配场景的标注规范和评测集。",
            "评审所有进入世界模型的数据接口。",
        ],
        "project": [
            "主导“灵枢-1”机械臂的桌面抓取感知升级，把长尾误抓率压到可发布水平。",
            "推动搭建跨传感器回放工具，让误检问题能直接回到原始片段。",
        ],
        "quotes": ["没有闭环数据，今天这会就到这。", "先给我长尾 case，不要先给结论。"],
    },
    {
        "name": "林桥",
        "slug": "lin_qiao",
        "department": "perception",
        "level": "P7",
        "role": "三维视觉算法工程师",
        "gender": "女",
        "mbti": "ISTJ",
        "personality": ["严谨", "安静", "执行稳定"],
        "culture": ["工程优先", "数据闭环"],
        "impression": "话不多，但一开口基本都是坐标系和标定链路的问题。",
        "responsibilities": [
            "负责深度相机标定、点云重建和工位级三维理解。",
            "维护机器人末端到世界坐标系的标定工具。",
            "支持装箱、拣选、插接等三维场景上线。",
        ],
        "project": [
            "搭过一套可视化标定巡检页，把现场标定偏移排查时间缩短到原来的三分之一。",
            "主导过点云去噪改造，让金属件反光场景的姿态估计稳定不少。",
        ],
        "quotes": ["这个不是模型问题，是标定链路先飘了。", "先把坐标系画出来，我们再继续。"],
    },
    {
        "name": "许棠",
        "slug": "xu_tang",
        "department": "perception",
        "level": "P7",
        "role": "世界模型研究员",
        "gender": "女",
        "mbti": "INFJ",
        "personality": ["抽象能力强", "追问本质", "耐心"],
        "culture": ["研究驱动", "长期主义"],
        "impression": "擅长把零散观测拼成统一状态表征，但很讨厌临时加 feature。",
        "responsibilities": [
            "负责操作场景的状态表征和短时预测模块。",
            "和规划组一起定义可供策略消费的世界状态接口。",
            "维护时序建模实验和离线评测基线。",
        ],
        "project": [
            "推动把多步抓取任务从单帧感知升级到短时状态预测，减少了遮挡带来的抖动。",
            "做过一版失败前兆预测模块，让策略切换更早更稳。",
        ],
        "quotes": ["别再往状态里塞 patch 了，先看抽象是不是错了。", "这个输入如果不可解释，后面所有策略都会飘。"],
    },
    {
        "name": "韩骁",
        "slug": "han_xiao",
        "department": "perception",
        "level": "P6",
        "role": "传感器融合工程师",
        "gender": "男",
        "mbti": "ESTP",
        "personality": ["行动快", "现场感强", "抗压"],
        "culture": ["问题导向", "结果导向"],
        "impression": "最擅长带着示波器和日志去现场抓融合链路的毛刺。",
        "responsibilities": [
            "负责相机、IMU、力传感器和编码器的融合链路。",
            "维护传感器同步、延迟补偿和降级策略。",
            "支援现场排查抖动、飘点和时序错乱问题。",
        ],
        "project": [
            "把力觉与视觉对齐流程做成标准脚本，减少了现场临时调参。",
            "主导过一次末端抖动排查，最后定位到 IMU 时间戳异常漂移。",
        ],
        "quotes": ["先看时间戳，八成不是模型炸了。", "别急着调参，先把链路拉齐。"],
    },
    {
        "name": "唐榆",
        "slug": "tang_yu",
        "department": "perception",
        "level": "P6",
        "role": "数据闭环算法工程师",
        "gender": "女",
        "mbti": "ENFP",
        "personality": ["节奏快", "组织能力强", "沟通主动"],
        "culture": ["闭环文化", "效率优先"],
        "impression": "能把一堆零散坏 case 收成结构化数据资产，是组里的闭环发动机。",
        "responsibilities": [
            "负责坏 case 挖掘、分桶和闭环优先级管理。",
            "维护标注指南、回放采样策略和问题台账。",
            "推动感知问题从线上回到训练集。",
        ],
        "project": [
            "做过长尾 case 分桶系统，让评测不再被平均指标掩盖。",
            "推动过一轮数据清洗，把脏标签对抓取识别的影响大幅收敛。",
        ],
        "quotes": ["这个 case 先别吵，先分桶。", "没有优先级的闭环，最后就是大家都很忙。"],
    },
    {
        "name": "顾准",
        "slug": "gu_zhun",
        "department": "planning",
        "level": "P8",
        "role": "任务规划负责人",
        "gender": "男",
        "mbti": "ENTJ",
        "personality": ["强推进", "结构化", "目标导向"],
        "culture": ["结果导向", "系统思维"],
        "impression": "特别擅长把模糊操作任务拆成可控状态机，不喜欢靠运气拿成功率。",
        "responsibilities": [
            "负责高层任务规划、技能编排和失败恢复策略。",
            "定义跨技能切换条件和任务终止标准。",
            "主导复杂装配任务的策略架构评审。",
        ],
        "project": [
            "把插接任务从单条脆弱轨迹改成分层技能编排，失败恢复率明显提升。",
            "主导建设任务级回放分析框架，能快速定位失败分支。",
        ],
        "quotes": ["先定义失败恢复，再讨论成功路径。", "不要把运气写进系统设计里。"],
    },
    {
        "name": "沈微",
        "slug": "shen_wei",
        "department": "planning",
        "level": "P7",
        "role": "运动规划工程师",
        "gender": "女",
        "mbti": "ISTP",
        "personality": ["冷静", "细节控", "工程稳"],
        "culture": ["安全优先", "工程纪律"],
        "impression": "对轨迹平滑性和碰撞边界特别敏感，宁可保守也不硬冲。",
        "responsibilities": [
            "负责机械臂轨迹生成、约束求解和碰撞检查。",
            "维护抓取、搬运、插接等动作库的参数边界。",
            "和硬件组一起调执行器极限与轨迹约束。",
        ],
        "project": [
            "把一套高频抖动动作改造成分段平滑轨迹，降低了执行器过热风险。",
            "做过狭窄工位的碰撞规避库，让部署稳定性提升明显。",
        ],
        "quotes": ["先看轨迹曲率，再谈速度。", "这个约束一放松，现场就会撞。"],
    },
    {
        "name": "罗砚",
        "slug": "luo_yan",
        "department": "planning",
        "level": "P7",
        "role": "强化学习工程师",
        "gender": "男",
        "mbti": "INTP",
        "personality": ["研究味重", "喜欢追因果", "不迷信大模型"],
        "culture": ["实验文化", "论文和工程并重"],
        "impression": "做 RL 很谨慎，最讨厌只给平均 reward 不给失败分布。",
        "responsibilities": [
            "负责抓取、开门、抽屉等操作任务的 RL 策略训练。",
            "维护奖励设计、离线评测和 sim2real 切换策略。",
            "支持任务规划组做策略能力边界定义。",
        ],
        "project": [
            "做过开门任务的课程学习改造，让训练曲线不再反复崩盘。",
            "搭过失败轨迹分析面板，方便快速看 reward design 是否有坑。",
        ],
        "quotes": ["先给我失败分布。", "这个 reward 写法会教会机器人偷懒。"],
    },
    {
        "name": "乔岚",
        "slug": "qiao_lan",
        "department": "planning",
        "level": "P6",
        "role": "具身策略研究员",
        "gender": "女",
        "mbti": "INFP",
        "personality": ["想象力强", "表达温和", "判断清晰"],
        "culture": ["研究驱动", "用户场景导向"],
        "impression": "喜欢把复杂场景先抽象成策略接口，讲话温和但边界很清楚。",
        "responsibilities": [
            "负责具身策略接口设计和跨任务泛化实验。",
            "研究语言条件、视觉条件下的技能组合方式。",
            "和世界模型组一起定义状态抽象层。",
        ],
        "project": [
            "推动把语言条件任务拆成可重用技能槽位，减少了策略重复开发。",
            "做过多任务策略泛化实验，帮团队厘清哪些能力值得沉淀为基础技能。",
        ],
        "quotes": ["先把技能接口抽象好，后面泛化才有意义。", "不要把一次成功误判成泛化能力。"],
    },
    {
        "name": "魏澄",
        "slug": "wei_cheng",
        "department": "planning",
        "level": "P6",
        "role": "控制算法工程师",
        "gender": "男",
        "mbti": "ESTJ",
        "personality": ["硬核", "执行强", "不怕现场"],
        "culture": ["工程优先", "稳定性优先"],
        "impression": "常年蹲真机，一听到高频振动就知道今天谁的锅最大。",
        "responsibilities": [
            "负责末端力控、阻抗控制和接触稳定性控制。",
            "维护真机参数表、控制器版本和调试记录。",
            "支援现场策略落地与安全边界设置。",
        ],
        "project": [
            "做过插接接触阶段的力控改造，让精细装配成功率稳定上了一个台阶。",
            "建立了真机参数对比表，避免版本回退时全靠猜。",
        ],
        "quotes": ["别再提成功率了，先看接触过程稳不稳。", "这个参数别直接改，先留版本。"],
    },
    {
        "name": "裴川",
        "slug": "pei_chuan",
        "department": "hardware",
        "level": "P8",
        "role": "机器人本体负责人",
        "gender": "男",
        "mbti": "ISTJ",
        "personality": ["稳重", "强标准化", "对风险敏感"],
        "culture": ["流程规范", "安全优先"],
        "impression": "最擅长把天马行空的本体需求压回材料、公差和量产现实里。",
        "responsibilities": [
            "负责机械臂本体架构、零部件选型和可靠性路线。",
            "把机械、电控、控制三侧的约束收拢成一套设计规则。",
            "评审所有新本体设计的安全性和可制造性。",
        ],
        "project": [
            "主导过一代机械臂减重改版，在不牺牲寿命的前提下把动态性能做上去。",
            "搭过本体设计 review 模板，避免后期才暴露装配死角。",
        ],
        "quotes": ["别只给我目标扭矩，把寿命也写出来。", "这个结构能不能量产，今天就要说清楚。"],
    },
    {
        "name": "程澈",
        "slug": "cheng_che",
        "department": "hardware",
        "level": "P7",
        "role": "关节执行器工程师",
        "gender": "男",
        "mbti": "INTJ",
        "personality": ["较真", "量化导向", "耐心"],
        "culture": ["硬件工程文化", "实测优先"],
        "impression": "专盯执行器效率、温升和寿命，不喜欢任何没测过的乐观假设。",
        "responsibilities": [
            "负责执行器方案选型、热设计和寿命测试。",
            "维护电机、减速器、驱动器配套参数库。",
            "跟控制组一起调高动态动作下的负载与电流限制。",
        ],
        "project": [
            "定位过一次关节热衰退问题，最后把温升模型和保护逻辑一起补齐。",
            "做过执行器寿命对比测试，为新一代本体节约了一轮试错成本。",
        ],
        "quotes": ["这个温升曲线先过了，我们再聊 demo。", "没寿命数据，别谈稳定交付。"],
    },
    {
        "name": "贺宁",
        "slug": "he_ning",
        "department": "hardware",
        "level": "P7",
        "role": "机械结构工程师",
        "gender": "女",
        "mbti": "ISFJ",
        "personality": ["细腻", "稳", "维护意识强"],
        "culture": ["工程优先", "协作友好"],
        "impression": "做结构时脑子里同时装着刚度、装配窗口和维修手册。",
        "responsibilities": [
            "负责夹爪、末端执行器和关键传动结构设计。",
            "维护装配图纸、BOM 版本和可维修性规范。",
            "配合供应链评估结构件可制造性和交期。",
        ],
        "project": [
            "做过一版快拆末端结构，减少了现场维护时间。",
            "优化过夹爪结构，让装配公差波动对效果的影响明显减小。",
        ],
        "quotes": ["这版图纸现场不好装，先别发。", "你现在省一个螺丝，后面会多两小时维修。"],
    },
    {
        "name": "宋越",
        "slug": "song_yue",
        "department": "hardware",
        "level": "P6",
        "role": "电控与嵌入式工程师",
        "gender": "男",
        "mbti": "ESTP",
        "personality": ["现场型", "反应快", "不怕脏活"],
        "culture": ["问题导向", "稳定性优先"],
        "impression": "板子一出毛病他总在现场第一排，带着逻辑分析仪和一脸没睡醒的样子。",
        "responsibilities": [
            "负责关节驱动板、传感器采集板和底层通信。",
            "维护嵌入式固件版本、参数表和调试工具。",
            "处理现场通信抖动、复位异常和电流保护问题。",
        ],
        "project": [
            "做过一轮 CAN 通信稳定性整治，把偶发复位问题打穿到底层时序。",
            "补齐过电控调试手册，减少了新人上手踩坑。",
        ],
        "quotes": ["先把波形抓下来。", "这是底层时序问题，不是上层又背锅。"],
    },
    {
        "name": "叶衡",
        "slug": "ye_heng",
        "department": "hardware",
        "level": "P6",
        "role": "安全与可靠性工程师",
        "gender": "女",
        "mbti": "ENTJ",
        "personality": ["原则强", "系统化", "风险前置"],
        "culture": ["安全文化", "流程规范"],
        "impression": "经常在最扫兴的时候说出最该说的话，所以大家最后都服她。",
        "responsibilities": [
            "负责危险源分析、失效模式评估和可靠性测试计划。",
            "维护跌落、碰撞、寿命等测试标准和结论记录。",
            "参与真机上线前的安全放行。",
        ],
        "project": [
            "主导过一轮末端夹持风险评审，提前拦住了一个可能伤人的方案。",
            "建立了失效模式库，让事故复盘不再靠记忆。",
        ],
        "quotes": ["这个风险不是低概率，是没人测。", "没有放行条件，就没有上线。"],
    },
    {
        "name": "江朔",
        "slug": "jiang_shuo",
        "department": "platform",
        "level": "P8",
        "role": "仿真平台负责人",
        "gender": "男",
        "mbti": "INTP",
        "personality": ["抽象能力强", "耐心", "架构控"],
        "culture": ["平台思维", "长期主义"],
        "impression": "总能把杂乱的实验流程压成一套平台能力，代价是他特别讨厌临时插队。",
        "responsibilities": [
            "负责仿真环境架构、任务编排和 sim2real 工具链。",
            "维护仿真资源调度、场景版本和接口标准。",
            "支撑规划、感知、控制多团队共用仿真底座。",
        ],
        "project": [
            "推动把多个零散仿真脚本收成统一任务平台，实验复现效率提升明显。",
            "做过一版 sim2real 差异看板，帮助团队定位现实落差来源。",
        ],
        "quotes": ["先把环境版本钉住。", "没有复现脚本的平台，最后都是情绪管理。"],
    },
    {
        "name": "苏禾",
        "slug": "su_he",
        "department": "platform",
        "level": "P7",
        "role": "数据引擎工程师",
        "gender": "女",
        "mbti": "INTJ",
        "personality": ["结构化", "标准化强", "执行稳"],
        "culture": ["数据治理", "自动化优先"],
        "impression": "对 schema 的执念近乎偏执，但也确实因此少了很多脏故障。",
        "responsibilities": [
            "负责数据 schema、样本版本、回放索引和数据血缘。",
            "维护多模态数据清洗、切分和发布流程。",
            "支持各算法团队快速拉取可复现实验集。",
        ],
        "project": [
            "推动统一多模态样本 schema，让不同团队终于能说同一种数据语言。",
            "做过数据血缘追踪，解决了实验结果无法回溯来源的问题。",
        ],
        "quotes": ["你先告诉我 schema，别先告诉我要加字段。", "没有血缘，后面谁都解释不清。"],
    },
    {
        "name": "陆沉",
        "slug": "lu_chen",
        "department": "platform",
        "level": "P7",
        "role": "训练基础设施工程师",
        "gender": "男",
        "mbti": "ISTP",
        "personality": ["冷静", "定位快", "不爱废话"],
        "culture": ["SRE", "工程效率"],
        "impression": "对 GPU 配额、容器镜像和训练失败率比谁都敏感，话很少但能稳住场面。",
        "responsibilities": [
            "负责训练集群、作业调度、镜像版本和资源配额。",
            "维护分布式训练脚本、故障模板和性能看板。",
            "支撑大模型、世界模型和策略训练共用基础设施。",
        ],
        "project": [
            "做过一轮训练集群容错治理，减少了大量半夜重跑。",
            "把镜像版本和依赖校验接入提交流程，减少“我这能跑”的扯皮。",
        ],
        "quotes": ["先给复现命令。", "这个不是模型挂了，是环境先脏了。"],
    },
    {
        "name": "白简",
        "slug": "bai_jian",
        "department": "platform",
        "level": "P6",
        "role": "云边协同平台工程师",
        "gender": "女",
        "mbti": "ESTJ",
        "personality": ["节奏快", "强责任心", "对线上敏感"],
        "culture": ["稳定性优先", "产品意识"],
        "impression": "很懂线上部署的痛点，总能提前把边端设备和云端平台的缝补好。",
        "responsibilities": [
            "负责边端模型发布、设备接入和云边数据回传。",
            "维护现场设备版本、灰度策略和回滚机制。",
            "支持真机部署到线上平台的链路稳定性。",
        ],
        "project": [
            "做过边端灰度平台，避免真机更新一把梭。",
            "优化过日志回传机制，让现场问题不再全靠口述。",
        ],
        "quotes": ["这个包别全量推，先灰度。", "没有回滚按钮的上线不叫上线。"],
    },
    {
        "name": "方珞",
        "slug": "fang_luo",
        "department": "platform",
        "level": "P6",
        "role": "工具链与评测工程师",
        "gender": "男",
        "mbti": "ENTP",
        "personality": ["爱琢磨工具", "表达直接", "推动力强"],
        "culture": ["工具化", "评测驱动"],
        "impression": "看到有人手工重复操作就坐不住，恨不得当场写个工具干掉。",
        "responsibilities": [
            "负责内部评测平台、实验看板和工具脚本。",
            "维护常用调试工具、批量回放和评测报告模板。",
            "支持各团队快速做版本对比和回归分析。",
        ],
        "project": [
            "做过统一评测报告模板，让跨组比较第一次变得没那么痛苦。",
            "把多项手工回放操作脚本化后，节省了大量重复时间。",
        ],
        "quotes": ["这事别再手工点了。", "先把评测模板统一，大家再比。"],
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_company_profile()
    for member in ROSTER:
        render_member(member)
    print(f"Generated {len(ROSTER)} materials in {OUTPUT_DIR}")


def write_company_profile() -> None:
    payload = {
        "company_name": COMPANY_NAME,
        "departments": {
            key: {
                "name": value["name"],
                "description": value["description"],
                "keywords": value["keywords"],
            }
            for key, value in DEPARTMENTS.items()
        },
    }
    payload["departments"]["general"] = {
        "name": "综合办公室",
        "description": "无法可靠归类时的默认部门。",
        "keywords": ["通用", "协调", "杂项"],
        "default": True,
    }
    (OUTPUT_DIR / "company_profile.yaml").write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def render_member(member: dict) -> None:
    department = DEPARTMENTS[member["department"]]
    frontmatter = {
        "name": member["name"],
        "slug": member["slug"],
        "company": COMPANY_NAME,
        "department": member["department"],
        "level": member["level"],
        "role": member["role"],
        "gender": member["gender"],
        "mbti": member["mbti"],
        "personality": member["personality"],
        "culture": member["culture"],
        "impression": member["impression"],
    }

    body = (
        f"# {member['name']}\n\n"
        f"## 一句话印象\n{member['impression']}\n\n"
        f"## 职责范围\n{bullets(member['responsibilities'])}\n\n"
        f"## 技术与方法\n{bullets(department['methods'])}\n\n"
        f"## 工作方式\n{bullets(department['workflow'])}\n\n"
        f"## 代表项目\n{bullets(member['project'])}\n\n"
        f"## 协作边界\n{bullets(department['boundary'])}\n\n"
        f"## 知识库\n{bullets(department['knowledge'])}\n\n"
        f"## 核心规则\n{bullets(department['rules'])}\n\n"
        f"## 表达风格\n{bullets(department['style'])}\n\n"
        f"## 决策方式\n{bullets(department['decisions'])}\n\n"
        f"## 协作行为\n{bullets(department['collaboration'])}\n\n"
        f"## 雷区\n{bullets(department['taboos'])}\n\n"
        f"## 典型话术\n{bullets(member['quotes'])}\n"
    )

    text = (
        f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()}\n---\n\n"
        f"{body}"
    )
    (OUTPUT_DIR / f"{member['slug']}.md").write_text(text, encoding="utf-8")


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


if __name__ == "__main__":
    main()
