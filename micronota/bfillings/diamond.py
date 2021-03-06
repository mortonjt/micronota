# ----------------------------------------------------------------------------
# Copyright (c) 2015--, micronota development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from os import stat, remove
from os.path import join, basename, splitext, exists
from logging import getLogger

import pandas as pd
from burrito.parameters import FlagParameter, ValuedParameter
from burrito.util import (
    ApplicationError, CommandLineApplication)
from skbio import read

from .util import _get_parameter
from ._base import MetadataPred
import string
import random

_OPTIONS_FLAG = {
    i: _get_parameter(FlagParameter, i)
    for i in [
            # only show alignments of forward strand
            '--forwardonly']}

_OPTIONS_VALUE = {
    i: _get_parameter(ValuedParameter, i, Delimiter=' ')
    for i in [
            '--threads',
            # 11 Gap open penalty.
            '--in',
            '--block-size',
            '--gapopen',
            # 1 Gap extension penalty.
            '--gapextend',
            # BLOSUM62 Scoring matrix.
            '--matrix',
            # Enable SEG masking of low complexity segments in the query.
            # (yes/no). The default is no for blastp and yes for blastx.
            '--seg',
            # -k 25 The maximum number of target sequences per query to
            # keep alignments for.
            '--max-target-seqs',
            # Keep alignments within the given percentage range of the top
            # alignment score for a query (overrides –max-target-seqs option).
            '--top',
            # -e 0.001 Maximum expected value to keep an alignment.
            '--evalue',
            # Minimum bit score to keep an alignment. Setting this option
            # will override the --evalue parameter.
            '--min-score',
            # Trigger the sensitive alignment mode with a 16x9 seed
            # shape config.
            '--sensitive',
            # Dynamic programming band for seed extension.
            '--band',
            # Compression for output file (0=none, 1=gzip).]
            '--compress',
            # Format of output file. (tab = BLAST tabular format;
            # sam = SAM format)
            '--outfmt']}

_OPTIONS_PATH = {
    i: _get_parameter(ValuedParameter, i, Delimiter=' ', IsPath=True)
    for i in [
            '--db',
            # -q Path to query input file in FASTA or FASTQ format
            # (may be gzip compressed).
            '--query',
            '--tmpdir',
            # -a
            '--daa',
            # output file
            '--out']}

_PARAMETERS = {}
_PARAMETERS.update(_OPTIONS_FLAG)
_PARAMETERS.update(_OPTIONS_VALUE)
_PARAMETERS.update(_OPTIONS_PATH)
_PARAMETERS_BLAST = {
    i: _PARAMETERS[i]
    for i in
    ['--threads',
     '--db',
     '--query',
     '--tmpdir',
     '--daa',
     '--gapopen',
     '--gapextend',
     '--matrix',
     '--max-target-seqs',
     '--top',
     '--evalue',
     '--min-score',
     '--sensitive',
     '--band',
     '--compress']}


class Diamond(CommandLineApplication):
    '''diamond controller.'''
    _command = 'diamond'
    _suppress_stderr = False

    # This re-implementation is required for subcommands
    def _get_base_command(self):
        if self._subcommand is None:
            raise ApplicationError('_subcommand has not been set.')
        # prevent append multiple subcommand
        if not self._command.endswith(self._subcommand):
            self._command = self._command_delimiter.join(
                [self._command, self._subcommand])
        return super()._get_base_command()

    BaseCommand = property(_get_base_command)

    def _accept_exit_status(self, exit_status):
        return exit_status == 0


class DiamondMakeDB(Diamond):
    '''diamond makedb controller.'''
    _subcommand = 'makedb'
    _parameters = {
        i: _PARAMETERS[i]
        for i in
        ['--in', '--block-size', '--threads', '--db']}


class DiamondBlastp(Diamond):
    '''diamond blastp controller.'''
    _subcommand = 'blastp'
    _parameters = _PARAMETERS_BLAST


class DiamondBlastx(Diamond):
    '''diamond blastp controller.'''
    _subcommand = 'blastx'
    _parameters = _PARAMETERS_BLAST


class DiamondView(Diamond):
    '''diamond view controller.'''
    _subcommand = 'view'
    _parameters = {
        i: _PARAMETERS[i]
        for i in
        ['--daa', '--out', '--outfmt', '--forwardonly']}


def make_db(in_fp, out_fp=None, params=None):
    '''Format database from a fasta file.

    This is similar to running ``diamond makedb --in db.faa --db db``.

    Parameters
    ----------
    in_fp : str
        Input path for the fasta file.
    out_fp : str or None (default)
        Output path for the formatted database file. It will be named
        after input file in the same directory by default.
    params : dict
        Other command line parameters for diamond blastp. key is the option
        (e.g. "-T") and value is the value for the option (e.g. "50").
        If the option is a flag, set the value to None.
    Returns
    -------
    int
        The exit code of the command.
    '''
    if out_fp is None:
        out_fp = splitext(in_fp)[0]
    app = DiamondMakeDB(InputHandler='_input_as_paths', params=params)
    app.Parameters['--in'].on(in_fp)
    app.Parameters['--db'].on(out_fp)
    res = app()
    res.cleanUp()
    return res


class FeatureAnnt(MetadataPred):
    '''
    Attributes
    ----------
    dat : list of str
        list of file path to databases.
    cache : list of skbio.Sequence
        list of skbio.Sequences to search against.
    '''
    def __init__(self, dat, out_dir, tmp_dir=None, cache=None):
        super().__init__(dat, out_dir, tmp_dir)
        self.cache = cache
        self.dat = dat

    def _annotate_fp(self, fp, aligner='blastp', evalue=0.001, cpus=1,
                     outfmt='tab', params=None):
        '''Annotate the sequences in the file.'''

        if self.has_cache():
            # Build cache
            self.cache.build()
            dbs = [self.cache.db] + self.dat
        else:
            dbs = self.dat

        found = []
        res = pd.DataFrame()
        seqs = []
        for db in dbs:
            out_prefix = splitext(basename(db))[0]
            daa_fp = join(self.out_dir, '%s.daa' % out_prefix)
            out_fp = join(self.out_dir, '%s.diamond' % out_prefix)
            self.run_blast(fp, daa_fp, db, aligner=aligner,
                           evalue=evalue, cpus=cpus, params=params)
            self.run_view(daa_fp, out_fp, params={'--outfmt': outfmt})
            res = res.append(self.parse_tabular(out_fp))

            found.extend(res.index)
            # save to a tmp file the seqs that do not hit current database
            new_fp = join(self.tmp_dir, '%s.fa' % out_prefix)
            with open(new_fp, 'w') as f:
                for seq in read(fp, format='fasta'):
                    if seq.metadata['id'] not in found:
                        seq.write(f, format='fasta')
                        seqs.append(seq)
            # no seq left
            if stat(new_fp).st_size == 0:
                break
            else:
                fp = new_fp

        # Update cache (inplace)
        if self.has_cache():
            self.cache.update(seqs)
            self.cache.close()
        return res

    def run_blast(self, fp, daa_fp, db, aligner='blastp', evalue=0.001, cpus=1,
                  params=None):
        '''Search query sequences against the database.

        Parameters
        ----------
        fp : str
            File path for the query sequence.
        daa_fp : str
            Output file path.
        cpus : int
            Number of CPUs. Default to 1. If it is set to 0, it will use
            all available CPUs.
        evalue : float
            Default to 0.01. Threshold E-value.
        params : dict
            Other command line parameters for diamond blastp. key is the option
            (e.g. "-T") and value is the value for the option (e.g. "50").
            If the option is a flag, set the value to None.

        Returns
        -------
        str
            The file path of the blast result.
        '''
        logger = getLogger(__name__)

        if aligner == 'blastp':
            app = DiamondBlastp
        elif aligner == 'blastx':
            app = DiamondBlastx
        else:
            raise ValueError('Unknown aligner: %s.' % aligner)

        blast = app(InputHandler='_input_as_paths', params=params)
        blast.Parameters['--query'].on(fp)
        blast.Parameters['--daa'].on(daa_fp)
        blast.Parameters['--db'].on(db)
        blast.Parameters['--evalue'].on(evalue)
        blast.Parameters['--threads'].on(cpus)
        blast.Parameters['--tmpdir'].on(self.tmp_dir)

        logger.info('Running: %s' % blast.BaseCommand)
        blast_res = blast()
        blast_res.cleanUp()
        return blast_res

    def run_view(self, daa_fp, out_fp, params=None):
        '''
        Parameters
        ----------
        daa_fp : str
            Input file resulting from diamond blast.
        out_fp : str
            Output file.
        '''
        logger = getLogger(__name__)
        view = DiamondView(InputHandler='_input_as_paths')
        view.Parameters['--daa'].on(daa_fp)
        view.Parameters['--out'].on(out_fp)
        logger.info('Running: %s' % view.BaseCommand)
        view_res = view()
        view_res.cleanUp()
        return view_res

    @staticmethod
    def parse_tabular(diamond_res, column='bitscore'):
        '''Parse the output of diamond blastp/blastx.

        Parameters
        ----------
        diamond_res : str
            file path
        column : str
            The column used to pick the best hits.

        Returns
        -------
        pandas.DataFrame
            The best matched records for each query sequence.
        '''
        columns = ['qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                   'gapopen', 'qstart', 'qend', 'sstart', 'send',
                   'evalue', 'bitscore']
        df = pd.read_table(diamond_res, names=columns)
        # pick the rows that have highest bitscore for each qseqid
        # df_max = df.groupby('qseqid').apply(
        #     lambda r: r[r[column] == r[column].max()])
        idx = df.groupby('qseqid')[column].idxmax()
        df_max = df.loc[idx]
        df_max.index = idx.index
        return df_max[['sseqid', 'evalue', 'bitscore']]

    @staticmethod
    def parse_sam(diamond_res, column=None, collapse=False):
        '''Parse the output of diamond blastp/blastx.

        Parameters
        ----------
        diamond_res : str
            file path
        column : str
            The column used to pick the best hits.

        Returns
        -------
        pandas.DataFrame
            The best matched records for each query sequence.
        '''
        seqs = read(diamond_res, format='sam')
        columns = ['qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                   'gapopen', 'qstart', 'qend', 'sstart', 'send',
                   'evalue', 'bitscore', 'sequence']
        df = pd.DataFrame(columns=columns)
        for i, seq in enumerate(seqs):
            s = str(seq)

            qseqid = seq.metadata['QNAME']
            sseqid = seq.metadata['RNAME']
            pident = seq.metadata['ZI']
            length = seq.metadata['ZL']
            mismatch = seq.metadata['CIGAR']
            gapopen = ''
            qstart = seq.metadata['POS']
            qend = ''
            sstart = seq.metadata['ZS']
            send = ''
            evalue = seq.metadata['ZE']
            bitscore = seq.metadata['ZR']
            row = pd.Series([qseqid, sseqid, pident,
                             length, mismatch, gapopen,
                             qstart, qend, sstart, send,
                             evalue, bitscore, s],
                            index=columns)
            df.loc[i] = row

        if column is not None:
            idx = df.groupby('qseqid')[column].idxmax()
            df_max = df.loc[idx]
            df_max.index = idx.index
            df = df_max[['sseqid', 'evalue', 'bitscore', 'sequence']]
        else:
            df = df[['sseqid', 'evalue', 'bitscore', 'sequence']]
        return df


class DiamondCache():
    '''
    Attributes
    ----------
    out_dir : str
        output directory file path
    fname : str
        fasta file to store cached sequences
    db : str
        diamond database to store cached sequences
    maxSize : int
        maxinum size of DiamondCache
    seqs : list of skbio.Sequence
        list of sequence objects
    '''
    def __init__(self, seqs=None, maxSize=200000, out_dir=""):
        self.out_dir = out_dir
        self.fname = self._generate_random_file()  # substitute for tempfile
        self.fasta = join(out_dir, '%s.fasta' % self.fname)
        self.db = join(out_dir, '%s.dmnd' % self.fname)
        self.maxSize = maxSize
        self.seqs = seqs

    def _generate_random_file(self, N=10):
        s = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(N))
        # look for unique filepath
        while exists(join(self.out_dir, s)):
            s = ''.join(random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits) for _ in range(N))
        return s

    def dbname(self):
        return self.db.name

    def is_empty(self):
        return (self.seqs is None) or len(self.seqs) == 0

    def build(self, params=None):
        for seq in self.seqs:
            seq.write(self.fasta, format='fasta')
        make_db(self.fasta, self.db, params)

    def update(self, seqs):
        """
        Parameters
        ----------
        seqs : list of skbio.Sequence
           List of sequences to update the cache.
        """
        self.seqs = seqs + self.seqs
        self.seqs = self.seqs[:self.maxSize]

    def close(self):
        remove(self.fasta)
        remove(self.db)
