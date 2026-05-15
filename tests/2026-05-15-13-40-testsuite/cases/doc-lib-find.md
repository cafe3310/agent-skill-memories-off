# Test Case: doc-lib-find

## ID & 标题
TC-1.5.2: 模糊检索文档

## 前置条件
1. 存在一个目录 `mock_docs/`，结构如下：
   - `projects/alpha.md`
   - `projects/beta.txt`
   - `archive/old.md`
   - `attachments/img.png`
2. `meta.md` 配置如下：
   ```yaml
   ---
   doc_root: ./mock_docs
   doc_extensions: .md
   doc_exclude_dirs: archive, attachments
   ---
   ```

## 输入/操作
执行指令：
`memocli find-doc-by-name --query alpha`

## 预期结果
1. 返回 `projects/alpha.md`。
2. 不返回 `beta.txt`（后缀不符）。
3. 不返回 `archive/old.md`（子目录被排除）。
4. 输出包含文档名、相对路径和长度。
