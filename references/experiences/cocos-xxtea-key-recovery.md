# Cocos JSB + XXTEA 加密资源密钥恢复

来源：Arrow Maze Master｜网赚包恢复2.0（thread `019ff049-966f-7283-89c0-94a9162889c6`）；同款方法上游来自 Cash-Arrows｜网赚包恢复2.0。案例落盘于 `08-package-recovery/Moving/arrow_maze_master/analysis/`（工作区证据，不随 skill 同步；案例实现脚本同样不随 skill 同步，需要时按下方规格自行实现）。

本条是参考经验，不是强制流程。命中"识别信号"才读取并参考；未命中直接跳过。

## 识别信号（全部满足才适用）

- Android 包，原生库为 ELF（arm64/aarch64），典型 `libcocos2djs.so` / `libcocos2d.so`。
- Cocos2d-x / Cocos Creator JS 绑定（JSB），入口为 `org.cocos2dx.javascript.*`。
- assets 中存在加密脚本 `.jsc`，或资源索引标记 `encrypted:true`。
- ELF dynsym 中出现 `jsb_set_xxtea_key`、`cocos2d::FileUtils::setFileKey`、`xxtea_decrypt` 中的任一符号。

命中后目标：从目标自身的 ELF 恢复密钥，并用目标自己的 payload 离线验证；不猜 key。

## 踩坑（家族级事实）

1. 参考常量泄漏：把参考包的 PLT 地址、槽位、偏移直接编译进"目标扫描器"，输出格式完全正确但内容全是参考包数值。修正：工具内任何地址都必须从目标自身 `.rela.plt` + `dynsym` 重新推导。
2. 单一工具地址不是事实：本家族案例中 Ghidra 展示地址比 ELF `st_value` 高 `0x100000`，数据指针表会被误判成 PLT 代码区。修正：`dynsym/st_value`、反汇编、`xxd` 原始字节三者一致才算"静态已证实"。
3. 结构公式要按目标验证：本家族库 PLT0 头 32 字节，`stub = .plt + (rela_idx + 2) * 16`；差一槽会把符号安到相邻函数。旁证：`jsb_set_xxtea_key` 实现尾调 `setFileKey` 的 stub，地址应与推导一致。
4. 找到调用点不是完成：callsite 只是假设，验收必须落在下游可验证产物。

## 成功方法（按序执行，可自建工具实现，不依赖案例脚本）

1. 定位符号与槽位：解析目标 ELF 的 `.dynsym` / `.dynstr` / `.rela.plt` / `.plt`：
   - 在 dynsym 中定位 `jsb_set_xxtea_key`、`FileUtils::setFileKey`、`xxtea_decrypt`；
   - 在 `.rela.plt` 中按符号索引（`r_info >> 32`）匹配，得到 GOT 槽 `r_offset`；
   - 先验证本库 PLT0 头占几个槽（本家族为 32 字节，即 2 个槽）：取第一个 stub 反汇编其 ADRP+ADD/LDR，若指向的 GOT 地址等于对应 rela 的 `r_offset`，则公式成立；
   - 槽位公式：`stub = .plt + (rela_idx + PLT0槽数) * 16`；
   - 旁证：`jsb_set_xxtea_key` 实现体应尾调 `setFileKey` 的 stub。
2. 扫描直接调用点（遍历可执行节）：
   - 按 imm26 解码 BL/B：`target = insn_addr + sign_extend(imm26) << 2`；
   - 命中步骤 1 推导出的 stub 即为直接调用点。
3. 提取字面量：
   - 在调用点前的指令窗口内找 `adrp/add` → `ldr q0, [xN]` → 栈上搭 SSO 字符串 → `bl setter`；
   - 16 字节 ASCII 字面量即密钥，其 hex 为 key；字面量必须位于目标自身节区。
4. 备选（无直接调用点时）：
   - 扫 `xxtea_decrypt` 调用点读取的 key 参数：ADRP/ADD 指向的 BSS `std::string` 对象；
   - 用 `.symtab` 的 `FILE_ENCRYPT_KEY` / `_crypto_key` 或反向引用确认语义；
   - 仍不行则运行时观察 setter/decrypt 参数（需设备），不作为静态结论。
5. 离线验收：
   - XXTEA 标准解密：little-endian、delta `0x9e3779b9`、key 右填充至 16 字节、密文尾部 4 字节为明文长度（需在合理区间）、解密结果可能是 gzip；
   - 对目标全部 `.jsc` 解密，JS 语法全过、明文 SHA-256 落盘才算完成。

自实现建议：纯 Python stdlib 或 Node stdlib 即可（ELF 解析用 `struct`，XXTEA 约 30 行）；人工交叉验证用 `readelf -W -S/-s/-r`、`objdump -d`、`xxd`。

## 完成标准

- 全部加密 payload 解密成功且语法校验通过，明文哈希落盘；结论标注"静态已证实（B 级）"。
- 运行时观察未做时，不得写成运行时闭环；密钥只解锁资源面，不闭合奖励/余额/资格链。
- 与参考包对比时，先对齐证据层级，再下结论。

## 不适用边界

- iOS/Mach-O、Windows/PE、Unity IL2CPP 等无 `.rela.plt`/`dynsym` 的格式：本条目细节不适用，需按各自格式找等价结构（如 Mach-O 的 `__la_symbol_ptr`/`__got`）并重新验证。
- 无 XXTEA/Cocos 符号的目标：直接跳过本条，不套用。
- 案例中的密钥值、地址、字面量偏移只属于原包，禁止迁移到任何其他项目。
