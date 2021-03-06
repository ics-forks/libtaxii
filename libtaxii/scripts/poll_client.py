#!/usr/bin/env python
# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import sys

import argparse
import dateutil.parser

import libtaxii as t
import libtaxii.scripts as scripts
import libtaxii.messages_11 as tm11
import libtaxii.clients as tc
import datetime


def main():
    parser = scripts.get_base_parser("Poll Client", path="/services/poll/")
    parser.add_argument("--collection", dest="collection", default="default", help="Data Collection to poll. Defaults to 'default'.")
    parser.add_argument("--begin_timestamp", dest="begin_ts", default=None, help="The begin timestamp (format: YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm) for the poll request. Defaults to None.")
    parser.add_argument("--end_timestamp", dest="end_ts", default=None, help="The end timestamp (format: YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm) for the poll request. Defaults to None.")
    parser.add_argument("--dest_dir", dest="dest_dir", default="", help="The directory to save Content Blocks to. Defaults to the current directory.")

    args = parser.parse_args()

    try:
        if args.begin_ts:
            begin_ts = dateutil.parser.parse(args.begin_ts)
            if not begin_ts.tzinfo:
                raise ValueError
        else:
            begin_ts = None

        if args.end_ts:
            end_ts = dateutil.parser.parse(args.end_ts)
            if not end_ts.tzinfo:
                raise ValueError
        else:
            end_ts = None
    except ValueError:
        print "Unable to parse timestamp value. Timestamp should include both date and time information along with a timezone or UTC offset (e.g., YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm). Aborting poll."
        sys.exit()

    poll_req = tm11.PollRequest(message_id=tm11.generate_message_id(),
                              collection_name=args.collection,
                              exclusive_begin_timestamp_label=begin_ts,
                              inclusive_end_timestamp_label=end_ts,
                              poll_parameters=tm11.PollRequest.PollParameters())

    print "Request:\n"
    if args.xml_output is False:
        print poll_req.to_text()
    else:
        print poll_req.to_xml(pretty_print=True)
        
    client = scripts.create_client(args)
    resp = client.callTaxiiService2(args.host, args.path, t.VID_TAXII_XML_11, poll_req.to_xml(pretty_print=True), args.port)
    r = t.get_message_from_http_response(resp, '0')
    
    print "Response:\n"
    if args.xml_output is False:
        print r.to_text()
    else:
        print r.to_xml(pretty_print=True)
    
    if r.message_type == tm11.MSG_POLL_RESPONSE:
        for cb in r.content_blocks:
            if cb.content_binding.binding_id == t.CB_STIX_XML_10:
                format = '_STIX10_'
                ext = '.xml'
            elif cb.content_binding.binding_id == t.CB_STIX_XML_101:
                format = '_STIX101_'
                ext = '.xml'
            elif cb.content_binding.binding_id == t.CB_STIX_XML_11:
                format = '_STIX11_'
                ext = '.xml'
            elif cb.content_binding.binding_id == t.CB_STIX_XML_111:
                format = '_STIX111_'
                ext = '.xml'
            else: # Format and extension are unknown
                format = ''
                ext = ''
            
            if cb.timestamp_label:
                date_string = 't' + cb.timestamp_label.isoformat()
            else:
                date_string = 's' + datetime.datetime.now().isoformat()
            
            filename = (args.dest_dir + r.collection_name + format + date_string + ext).translate(None, '/\\:*?"<>|')
            f = open(filename, 'w')
            f.write(cb.content)
            f.flush()
            f.close()
            print "Wrote Content Block to %s" % filename

if __name__ == "__main__":
    main()
