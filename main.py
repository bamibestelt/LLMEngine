import argparse
import threading

from privateGPT import PrivateGPT
from rabbit import start_listen_prompt, start_listen_data_update_request


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
            # start_blog_links_request()
            PrivateGPT().init_llm_qa()
            PrivateGPT().qa_prompt("what is a software")
        return
    else:
        print("start listening to requests")
        # listen to data-update request
        data_update_thread = threading.Thread(target=start_listen_data_update_request)
        # listen to prompt
        prompt_thread = threading.Thread(target=start_listen_prompt)
        data_update_thread.start()
        prompt_thread.start()
        data_update_thread.join()
        prompt_thread.join()


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

