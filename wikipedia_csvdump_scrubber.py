import csv
from sys import argv
import os
import pandas as pd
import time

def binary_search_pageid(page_scrubbed_path, target):
    with open(page_scrubbed_path, mode='r', newline='', encoding='utf-8') as page_scrubbed_file:
        reader = csv.reader(page_scrubbed_file)
        start, end = 0, sum(1 for row in page_scrubbed_file) - 1
        page_scrubbed_file.seek(0)

        while start <= end:
            mid = (start + end) // 2
            page_scrubbed_file.seek(0)
            for _ in range(mid):
                next(reader)
            row = next(reader)
            mid_value = int(row[0])

            if mid_value == target:
                return row[1]
            elif mid_value < target:
                start = mid + 1
            else: 
                end = mid - 1
    return None


def category_items_search(catlinks_path, head, item_set):
    item_set.add(head)
    print(head)
    if head.startswith('Category:'):
        print('here')
        with open(catlinks_path, mode='r', newline='', encoding='latin-1') as catlinks_file:
            catlinks = csv.reader(catlinks_file)
            found = False
            for row in catlinks:
                if ('Category:'+row[1]) == head:
                    item_set.update(category_items_search(catlinks_path, row[0], item_set))
                    found = True
                elif found:
                    break
    return item_set


# def trash_catlink_removal(page_scrubbed_path, catlinks_path):

#     with open(catlinks_path, mode='r', newline='', encoding='latin-1') as catlinks_file, \
#          open(page_scrubbed_path, mode='r', newline='', encoding='latin-1') as page_scrubbed_file:
#         catlinks = csv.reader(catlinks_file)
#         page = csv.reader(page_scrubbed_file)
#         pages = set()
#         for row in page:
#             pages.add(row[1])
#         print(len(pages))
#         for i,row in enumerate(catlinks):
#             if ('Category:'+row[1]) not in pages:
#                 print(row)

#     pass



def catlinks_scrubber(catlinks_path, page_scrubbed_path):

    # Create dictionary from page csv. 
    # The key is the page_id which is cl_to in the categorylinks table
    # The value is the page_title
    # Creates set of page_title
    # Used to assure categorylinks are valid and to remove trash
    page_dict = {}
    page_set = set()
    with open(page_scrubbed_path, mode='r', newline='', encoding='latin-1') as page_scrubbed_file:
        reader = csv.reader(page_scrubbed_file)
        for row in reader:
            page_dict[row[0]] = row[1]
            page_set.add(row[1])

    # Removes all unnecessary data from category links      
    # Only keep cl_to and cl_from
    # Only keeps links that are from categories that exist in the page table
    # Only keeps links that point to categories or articles that exist in the page table
    # Only keeps primary links, removes all links to redirects and from redirects
    # https://www.mediawiki.org/wiki/Manual:Categorylinks_table
    # 25.38GB -> 4.67GB
    catlinks_scrubbed_path = os.path.splitext(catlinks_path)[0] + '_scrubbed.csv'
    with open(catlinks_path, mode='r', newline='', encoding='latin-1') as catlinks_file, \
         open(catlinks_scrubbed_path, mode='w', newline='', encoding='latin-1') as catlinks_scrubbed_file:
        reader = csv.reader(catlinks_file)
        writer = csv.writer(catlinks_scrubbed_file)
        for row in reader:
            if (row[0] in page_dict.keys()) and (('Category:'+row[1]) in page_set):
                writer.writerow([page_dict[row[0]],row[1]])
                
    # Sort the reduced csv
    # TO DO: Implement some sort of chunk merge sort to reduce memory usage
    df = pd.read_csv(catlinks_scrubbed_path)
    df_sorted = df.sort_values(by=[df.columns[1], df.columns[0]])
    df_sorted.to_csv(catlinks_scrubbed_path, index=False)

def simple_page_scrubber(page_path, page_scrubbed_path):
    # Remove all pages that are not articles or categories
    # This is defined by the page_namespace, 0 for articles and 14 for categories
    # Remove all redirect pages, this is defined by a 1 in the page_is_redirect field
    # Remove unnecessary data, only keep the page_id and page_title
    # https://www.mediawiki.org/wiki/Manual:Page_table
    # 6.15GB -> 317MB
    with open(page_path, mode='r', newline='', encoding='latin-1') as page_file, \
         open(page_scrubbed_path, mode='w', newline='', encoding='latin-1') as page_scrubbed_file:
        reader = csv.reader(page_file)
        writer = csv.writer(page_scrubbed_file)
        for row in reader:
            if row[3] == '0':
                if row[1] == '0':
                    writer.writerow([row[0],row[2]])
                elif row[1] == '14':
                    writer.writerow([row[0],'Category:'+row[2]])


def scrubber(page_path, catlinks_path):

    page_scrubbed_path = os.path.splitext(page_path)[0] + '_scrubbed.csv'
    simple_page_scrubber(page_path, page_scrubbed_path)

    catlinks_scrubbed_path = os.path.splitext(catlinks_path)[0] + '_scrubbed.csv'


    catlinks_scrubber(catlinks_path, page_scrubbed_path)

    head = 'Category:Boolean_algebra'
    hidden_category_set = set()
    hidden_category_set = category_items_search(catlinks_scrubbed_path, head, hidden_category_set)
    print(hidden_category_set)
    print(len(hidden_category_set))


    pass


def main(page_path, catlinks_path):
    t = time.time()
    scrubber(page_path, catlinks_path)
    print(time.time()-t)

if __name__ == "__main__":
    main(argv[1], argv[2])