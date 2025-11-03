import pandas as pd
from pathlib import Path
from utility.utilities import load_config

class merge:
    def __init__(self, df_path_hashtag_7: Path, df_path_hashtag_30: Path, merged_data_path_hashtag: Path,
                 df_path_song_7: Path, df_path_song_30: Path, merged_data_path_song: Path):
        self.df_path_hashtag_7 = df_path_hashtag_7
        self.df_path_hashtag_30= df_path_hashtag_30
        self.df_path_song_7 = df_path_song_7
        self.df_path_song_30 = df_path_song_30
        self.merged_data_path_hashtag = merged_data_path_hashtag
        self.merged_data_path_song = merged_data_path_song

    def merge_and_save_hashtags(self):
        df1 = pd.read_csv(self.df_path_hashtag_7)   
        df2 = pd.read_csv(self.df_path_hashtag_30)
        merged = pd.merge(df1, df2, on="hashtag", how="outer", suffixes=("_30days", "_7days"))
        merged["recurring"] = merged.apply(
            lambda row: 1 if pd.notnull(row["post_no_30days"]) and pd.notnull(row["post_no_7days"]) else 0,
            axis=1
        )
        merged.to_csv(self.merged_data_path_hashtag, index=False)
        print("Done merging hashtags Datasets")

    def merge_and_save_songs(self):
        df1 = pd.read_csv(self.df_path_song_7)   
        df2 = pd.read_csv(self.df_path_song_30)
        merged = pd.merge(df1, df2, on="song", how="outer", suffixes=("_30days", "_7days"))
        merged["recurring"] = merged.apply(
            lambda row: 1 if pd.notnull(row["artist_30days"]) and pd.notnull(row["artist_7days"]) else 0,
            axis=1
        )
        merged.to_csv(self.merged_data_path_song, index=False)
        print("Done merging song Datasets")

    def merge(self):
        self.merge_and_save_hashtags()
        self.merge_and_save_songs()

if __name__ == "__main__":
    config_file = Path("config.yaml");
    config= load_config(config_file)

    path7_hashtag = Path(config["path"]["hashtags"]["past_7_days"])
    path30_hashtag = Path(config["path"]["hashtags"]["past_30_days"])
    merged_data_path_hashtag = Path(config["path"]["merge"]["hashtag"])

    path7_song = Path(config["path"]["songs"]["past_7_days"])
    path30_song = Path(config["path"]["songs"]["past_30_days"])
    merged_data_path_song= Path(config["path"]["merge"]["song"])

    merge_obj = merge(path7_hashtag, path30_hashtag, merged_data_path_hashtag, path7_song, path30_song, merged_data_path_song)
    merge_obj.merge()
    print("Done merging Datasets")
