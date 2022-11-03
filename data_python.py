from datetime import datetime
import sys
import pandas as pd
import ast
from matplotlib import rcParams


def main(file_name: str):
    df = pd.read_csv(file_name)
    df_columns = ["title", "technologies", "experience"]
    df = df.loc[:, df_columns].copy()
    df = df.dropna()
    technologies_list = [ast.literal_eval(technologies) for technologies in df["technologies"]]
    df["technologies"] = technologies_list

    technologies_flat = df["technologies"].explode()

    df = df.join(pd.crosstab(technologies_flat.index, technologies_flat))
    df = df.drop(columns=["experience", "title", "technologies"])

    now = datetime.now().today()
    png_name = f"./data_png/top-python-technologies-{now.date()}.png"
    rcParams.update({'figure.autolayout': True})
    top_technologies = df.sum().sort_values(ascending=False).iloc[:28]
    top_technologies.plot.bar(title=f'The most demanded technologies \n {now.date()}').figure.savefig(png_name)


if __name__ == "__main__":
    file_name = sys.argv[1]
    main(file_name)
