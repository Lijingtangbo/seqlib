'''
ENCODE relevant functions and classes
'''

import requests
import requests.compat

__author__ = 'Xiao-Ou Zhang <kepbod@gmail.com>'


class Entry(object):
    '''
    Meta class of ENCODE entry
    '''
    def __init__(self, eid, etype=None, json_d=None):
        if etype is None:
            raise Exception('etype should not be None!')
        self.accession = eid
        self.id = '/%s/%s/' % (etype, eid)
        self.baseurl = 'https://www.encodeproject.org/'
        self.url = requests.compat.urljoin(self.baseurl, self.id)
        if json_d is None:
            self.json = self._fetch_json()  # fetch json form encode
        else:
            self.json = json_d

    def _fetch_json(self):
        '''
        Fetch json file from ENCODE
        '''
        headers = {'accept': 'application/json'}
        response = requests.get(self.url, headers=headers)
        return response.json()


class SeqFile(Entry):
    '''
    Meta class of ENCODE file entry
    '''
    def __init__(self, fid, json_d=None):
        entry_type = 'file'
        super(SeqFile, self).__init__(fid, entry_type, json_d=json_d)
        self._parse_file_json()

    def _parse_file_json(self):
        # experiment info
        self.exp = self.json['dataset']
        try:
            replicate = self.json['replicate']
            biorep = 'biological_replicate_number'
            tchrep = 'technical_replicate_number'
            self.biological_replicate = replicate[biorep]
            self.technical_replicate = replicate[tchrep]
            self.is_stranded = replicate['library']['strand_specificity']
        except KeyError:
            replicate = self.json['technical_replicates'][0].split('_')
            self.biological_replicate = replicate[0]
            self.technical_replicate = replicate[1]
            self.is_stranded = False
        # file info
        self.file_type = self.json['file_type']
        self.status = self.json['status']
        self.file_url = requests.compat.urljoin(self.baseurl,
                                                self.json['href'])
        self.file_md5 = self.json['md5sum']
        self.file_size = self.json['file_size']


class RawFile(SeqFile):
    '''
    ENCODE raw file entry.
    >>> f = RawFile('ENCFF037JQC')
    >>> str(f.exp)
    '/experiments/ENCSR362AIZ/'
    >>> f.biological_replicate
    1
    >>> f.technical_replicate
    1
    >>> f.is_stranded
    False
    >>> str(f.file_type)
    'fastq'
    >>> str(f.status)
    'released'
    >>> str(f.file_url)
    'https://www.encodeproject.org/files/ENCFF037JQC/@@download/ENCFF037JQC.fastq.gz'
    >>> str(f.file_md5)
    'e5f5ef9f88ef582526cf1a54023f5ad0'
    >>> f.file_size
    1925682263
    >>> str(f.run_type)
    'single-ended'
    >>> f.read_length
    101
    '''
    def __init__(self, fid, json_d=None):
        super(RawFile, self).__init__(fid, json_d=json_d)
        self._parse_rawfile_json()

    def _parse_rawfile_json(self):
        self.run_type = self.json['run_type']
        self.read_length = self.json['read_length']


class ProcessedFile(SeqFile):
    '''
    ENCODE processed file entry.
    >>> f = ProcessedFile('ENCFF281ENU')
    >>> str(f.exp)
    '/experiments/ENCSR362AIZ/'
    >>> f.biological_replicate
    2
    >>> f.technical_replicate
    1
    >>> f.is_stranded
    False
    >>> str(f.file_type)
    'bam'
    >>> str(f.status)
    'released'
    >>> str(f.file_url)
    'https://www.encodeproject.org/files/ENCFF281ENU/@@download/ENCFF281ENU.bam'
    >>> str(f.file_md5)
    '9559d1c9df631fc7b5069a442e38ae16'
    >>> f.file_size
    4400306818
    >>> str(f.assembly)
    'mm10'
    >>> str(f.output_type)
    'alignments'
    '''
    def __init__(self, fid, json_d=None):
        super(ProcessedFile, self).__init__(fid, json_d=json_d)
        self._parse_processedfile_json()

    def _parse_processedfile_json(self):
        self.assembly = self.json['assembly']
        self.output_type = self.json['output_type']


class Exp(Entry):
    '''
    ENCODE experiment entry
    >>> exp = Exp('ENCSR362AIZ')
    >>> str(exp.accession)
    'ENCSR362AIZ'
    >>> str(exp.id)
    '/experiments/ENCSR362AIZ/'
    >>> str(exp.url)
    'https://www.encodeproject.org/experiments/ENCSR362AIZ/'
    >>> str(exp.description)
    'Total RNA-Seq on postnatal 0 day mouse forebrain'
    >>> str(exp.assay)
    'RNA-seq'
    >>> for f in exp.fetch_file(raw=True):
    ...     print(f.accession)
    ENCFF447EXU
    ENCFF037JQC
    ENCFF458NWF
    ENCFF358MFI
    >>> for f in exp.fetch_file(file_type='bam'):
    ...     print(f.accession)
    ENCFF428JNJ
    ENCFF112PJJ
    ENCFF694GJR
    ENCFF738MJJ
    ENCFF249QVN
    ENCFF380XIS
    ENCFF047GZO
    ENCFF811VPO
    ENCFF281ENU
    ENCFF916AXO
    >>> for f in exp.fetch_file(file_type=['bam', 'bigWig']):
    ...     print(f.accession)
    ENCFF428JNJ
    ENCFF503VVW
    ENCFF592ZRF
    ENCFF112PJJ
    ENCFF694GJR
    ENCFF941BPF
    ENCFF285HFJ
    ENCFF738MJJ
    ENCFF100LGI
    ENCFF249QVN
    ENCFF380XIS
    ENCFF623UHM
    ENCFF461GSJ
    ENCFF010GFV
    ENCFF047GZO
    ENCFF811VPO
    ENCFF281ENU
    ENCFF916AXO
    ENCFF190EHR
    ENCFF564LUK
    ENCFF372TAA
    ENCFF326RPH
    '''
    def __init__(self, exp):
        entry_type = 'experiments'
        super(Exp, self).__init__(exp, entry_type)
        self._parse_exp_json()

    def _parse_exp_json(self):
        self.description = self.json['description']
        self.assay = self.json['assay_term_name']

    def fetch_file(self, raw=False, file_type=None):
        file_json = self.json['files']
        for f in file_json:
            if f['output_category'] == 'raw data':
                is_raw = True
            else:
                is_raw = False
            if raw == is_raw:
                fid = f['accession']
                if is_raw:
                    yield RawFile(fid, json_d=f)
                else:
                    if file_type is not None:
                        if isinstance(file_type, list):
                            if f['file_type'] in file_type:
                                yield ProcessedFile(fid, json_d=f)
                        elif file_type == f['file_type']:
                            yield ProcessedFile(fid, json_d=f)
                    else:
                        yield ProcessedFile(fid, json_d=f)


if __name__ == '__main__':
    import doctest
    doctest.testmod()