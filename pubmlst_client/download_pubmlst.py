#!/usr/bin/env python

import argparse
import json
import os
import re
import urllib.request
import sys
import time
import datetime

from pubmlst_client.util import get


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", "-o", dest="outdir", default='./mlstdb', help="output directory")
    parser.add_argument("--base-url", "-b", dest="base_url", default='http://rest.pubmlst.org/db', help="Base URL for the API. Suggested values are: http://rest.pubmlst.org/db (default), https://bigsdb.pasteur.fr/api/db")
    args = parser.parse_args()

    api_url_base = args.base_url

    url_base_response = json.loads(get(api_url_base))

    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)

    for db in url_base_response:
        databases =  db['databases']
        for database in databases:
            # rmlst is a rescrited database
            if 'rmlst' in database['name'] or 'test' in database['name']:
                continue
            if '_seqdef' in database['name']:
                db_download_path_1 = '%s/%s' % (args.outdir,database['name'][8:-7])
                # Find MLST Schemes
                schemes = json.loads(get(''.join([database['href'],'/schemes'])))
                mlst_schemes = []
                for scheme in schemes['schemes']:
                    # The desription element is has some inconsistancies; this list is to navigate those.
                    if 'MLST' == scheme['description'] or "MLST" in  scheme['description'].split(' ') and  not "Extended MLST" == scheme['description']:
                        if  'MLST (Pla-Díaz)' == scheme['description'] and database['name'][8:-7] == 'tpallidum':
                            continue
                        mlst_schemes.append(scheme['scheme'].split('/')[-1])
                mlst_schemes.sort()
                for i in range(len(mlst_schemes)):
                    # Folders in MLST script folders are named after the organism if scheme is 1. If scheme number lager than 1 then name is organisms with sheme number appended on.
                    if int(mlst_schemes[i])> 1:
                        db_download_path = db_download_path_1 + "_%s" % (mlst_schemes[i])
                        os.mkdir(db_download_path)
                    else:
                        db_download_path = db_download_path_1
                        os.mkdir(db_download_path)
                    plaintext_header = {'Content-Type': 'text/plain'}
                    types_tsv = get(''.join([database['href'],'/schemes/%s/profiles_csv' % mlst_schemes[i]]), headers=plaintext_header).decode('utf-8')
                    if int(mlst_schemes[i])> 1:
                        output_filename = os.path.join( db_download_path , database['name'][8:-7] + '_%s'% (mlst_schemes[i]) +'.txt')
                    else:
                        output_filename = os.path.join( db_download_path , database['name'][8:-7] + '.txt')
                    with open(output_filename, 'w') as f:
                        f.write(types_tsv)
                    log_msg = {
                            'timestamp': str(datetime.datetime.now().isoformat()),
                            'event': 'file_downloaded',
                            'filename': output_filename,
                        }
                    print(json.dumps(log_msg), file=sys.stderr)
                    db_res = json.loads(get(''.join([database['href'],'/schemes/%s' % mlst_schemes[i]])))
                    for locus_url in db_res['loci']:
                        locus = json.loads(get(locus_url))
                        alleles_fasta = get(locus['alleles_fasta'], headers=plaintext_header).decode('utf-8')
                        output_filename = os.path.join(db_download_path, locus['id'] + '.fasta')
                        with open(output_filename, 'w') as f:
                            f.write(alleles_fasta)
                        log_msg = {
                            'timestamp': str(datetime.datetime.now().isoformat()),
                            'event': 'file_downloaded',
                            'filename': output_filename,
                        }
                        print(json.dumps(log_msg), file=sys.stderr)

if __name__ == '__main__':
    main()
