import argparse

from rabbit import start_listen_prompt, start_listen_data_update_request

test_rss = "https://deviesdevelopment.github.io/blog/posts/index.xml"


def listen_to_ingestion_request():
    args = parse_arguments()
    if args.t:
        print("test llm respond with hardcoded data")
        while True:
            query = input("\nput anything to start test: ")
            if query == "exit":
                break
            if query.strip() == "":
                continue
            # start_listen_data_update_request()
            # start_listen_prompt()
        return
    else:
        print("start listening to requests")
        # listen to data-update request
        start_listen_data_update_request()
        # listen to prompt
        start_listen_prompt()


def parse_arguments():
    parser = argparse.ArgumentParser(description='Ingest documents.')
    parser.add_argument("-t",
                        action='store_true',
                        help='Use this flag to use test rss defined in the code.')

    parser.add_argument("-r",
                        action='store_true',
                        help='Use this flag to listen to trigger from frontend.')

    return parser.parse_args()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    listen_to_ingestion_request()

