import utils
from src.database.azure_cosmos import AzureCosmos
from src import scrapers

import argparse
import asyncio
import multiprocessing


if __name__ == "__main__":
    num_cpus = multiprocessing.cpu_count()

    parser = argparse.ArgumentParser(description="Scraper script")
    parser.add_argument("--scraper_name", type=str, required=True, help="scraper name")
    parser.add_argument("--vm_offset", type=int, default=1000, help="VM offset for processing URLs")
    parser.add_argument("--batch_size", type=int, default=100, help="Number of URLs to process per batch")
    parser.add_argument("--vm_name", type=str, default="local", help="Name of the VM used for processing flag")
    args = parser.parse_args()

    print(f"Detected {num_cpus} CPUs on {args.vm_name}\nVM_OFFSET: {args.vm_offset}\nBATCH_SIZE: {args.batch_size}.")

    DATABASE, CONTAINER = "Scraper", args.scraper_name
    # TODO: make sure async is working here
    azure_cosmos = AzureCosmos(DATABASE, CONTAINER)

    try:
        asyncio.run(
            utils.process_urls_concurrently(
                azure_cosmos=azure_cosmos,
                scraper_name=args.scraper_name,
                vm_offset=args.vm_offset,
                batch_size=args.batch_size,
                max_workers=num_cpus + 1,
                vm_name=args.vm_name,
            )
        )
    except Exception as e:
        import traceback
        print(f"An error occurred: {traceback.format_exc()}")
