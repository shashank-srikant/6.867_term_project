import pandas as pd
import sys

if __name__ == '__main__':
    fname1 = sys.argv[1]
    fname2 = sys.argv[1]
    df = pd.read_csv("csv/"+fname1+".csv")
    df.to_latex("csv/"+fname2+".tex",float_format='%.2f', index=False)

