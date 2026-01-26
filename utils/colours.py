import altair as alt

def build_global_color_scale(values):
    return alt.Scale(domain=sorted(values), scheme="category20")