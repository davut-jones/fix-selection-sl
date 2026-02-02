import altair as alt

def build_global_color_scale(values):
    return alt.Scale(domain=sorted(values), scheme="category20")


### dark  → light

# blue
# 1f77b4  →  #aec7e8

# orange
# ff7f0e  →  #ffbb78

# green
# 2ca02c  →  #98df8a

# red
# d62728  →  #ff9896

# purple
# 9467bd  →  #c5b0d5

# brown
# 8c564b  →  #c49c94

# pink
# e377c2  →  #f7b6d2

# grey
# 7f7f7f  →  #c7c7c7

# olive / yellow-green
# bcbd22  →  #dbdb8d

# teal / cyan
# 17becf  →  #9edae5