from data_collector import DataCollector


def main():

    collector = DataCollector()

    df_canada_rate = collector.get_canada_policy_rate()

    # df_selic = collector.get_selic()

    # df_canada_cpi = collector.get_canada_cpi()


if __name__ == "__main__":
    main()