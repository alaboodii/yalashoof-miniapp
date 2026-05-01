"""Add a test sub_filter to verify __ext2 block sub_filters fire."""
p = "/etc/nginx/sites-available/yala.zaboni.store"
with open(p) as f:
    c = f.read()

# Find the __ext2 block's </body> sub_filter and prepend a test
OLD = '        sub_filter "</body>" "<a id=\\"alab-home"'
TEST = '        sub_filter "<body>" "<body><!--EXT2-FILTER-FIRED-->";\n'

idx = c.find(OLD)
if idx >= 0:
    # Find the SECOND occurrence (in __ext2 block, since / block also has alab-home with /shoot/)
    # Actually we know there's only one alab-home with href="/" — the korasimo __ext2 block.
    # But let me find where __ext2 block starts and look from there.
    ext2_idx = c.find('location ~ "^/__ext2?')
    if ext2_idx > 0:
        idx = c.find(OLD, ext2_idx)
    if idx > 0:
        c = c[:idx] + TEST + c[idx:]
        with open(p, "w") as f:
            f.write(c)
        print("Test sub_filter added to __ext2 block")
    else:
        print("FAIL: __ext2 </body> marker not found")
else:
    print("FAIL: alab-home marker not found")
