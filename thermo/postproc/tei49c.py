# %%
import pandas as pd
import sqlite3
import zipfile

file = "C:\Users\localadmin\Documents\data\minix\thermo\tei49c\tei49c_all_lrec-20221125204600.dat"
year = 2022

# %%
def read_tei49c_file(file: str, year: int):
    try:
        year = str(year) + "-"

        print(f"Processing {file} ...")
        df = pd.DataFrame()

        if ".zip" in file:
            with zipfile.ZipFile(file=file, mode="r") as zf:
                for file in zf.namelist():
                    with zf.open(file, mode="r") as obj:
                        df
                        df = pd.read_csv(obj, sep="\s+", engine='python')
        else:
            df = pd.read_csv(file, sep="\s+", engine='python')
            df.reset_index(inplace=True)
                        if "level_0" in df.columns:
                            df.rename(columns={'level_0': 'pcdate', 'level_1': 'pctime'}, inplace=True)
                        if "pcdate" in df.columns:
                            df['dtm'] = pd.to_datetime(df['pcdate'] + ' ' + df['pctime'])
                        else:
                            if "tei49c" in tbl:
                                df['dtm'] = pd.to_datetime(year + df['date'] + ' ' + df['time'])
                            else:
                                df['dtm'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                        df['source'] = os.path.join(archive, file)
                        if 'hio3' in df.columns:
                            df.drop(columns='hio3', inplace=True)
                        if 'o3lt' in df.columns:
                            df.drop(columns='o3lt', inplace=True)
                        df.set_index('dtm', inplace=True)
                        if 'index' in df.columns:
                            df.drop(columns='index', inplace=True)
                        res = df2sqlite.df2sqlite(df, db, tbl)
    except Exception as err:
        print(err)



# def 


# CREATE TABLE "tei49c_hourly" (
# 	"dtm"	TIMESTAMP NOT NULL,
# 	"o3"	REAL,
# 	"sdo3"	REAL,
# 	"no3"	REAL,
# 	"flags"	TEXT,
# )
