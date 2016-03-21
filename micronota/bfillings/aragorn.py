from burrito.parameters import FlagParameter, ValuedParameter

from .util import _get_parameter

class Aragorn(CommandLineApplication):
    ''' Aragorn application controller '''
    _command = 'aragorn'
    _valued_path_options = [
        # <outfile>  print output into <outfile>. If <outfile>
        #          exists, it is overwritten.
        #          By default, output goes to STDOUT.
        '-o'

    ]
    _valued_nonpath_options = [
        # Use the GenBank transl_table = <num> genetic code.
        '-gc',
        # B = A,C,G, or T. <aa> is the three letter
        # code for an amino-acid. More than one modification
        # can be specified. eg -gcvert,aga=Trp,agg=Trp uses
        # the Vertebrate Mitochondrial code and the codons
        # AGA and AGG changed to Tryptophan.
        ',BBB',
        # <max> Search for tRNA genes with introns in
        # anticodon loop with maximum length <max>
        # bases. Minimum intron length is 0 bases.
        # Ignored if -m is specified.
        # Search for tRNA genes with introns in
        # anticodon loop with maximum length <max>
        # bases, and minimum length <min> bases.
        # Ignored if -m is specified.
        '-i',
        # Change scoring thresholds to <num> percent of default levels.
        '-ps',
        # Search for tmRNA genes.
        '-m',
        # Search for tRNA genes.
        # By default, both are detected. If one of
        # -m or -t is specified, then the other
        # is not detected unless specified as well.
        '-t',
        # Search for Metazoan mitochondrial tRNA
        # genes. -i switch ignored. Composite
        # Metazoan mitochondrial genetic code used.
        '-mt',
        # Search for Mammalian mitochondrial tRNA
        # genes. -i switch ignored. -tv switch set.
        # Mammalian mitochondrial genetic code used.
        '-mtmam',
        # Same as -mt but low scoring tRNA genes are
        # not reported.
        '-mtx',
        # Use standard genetic code.
        '-gcstd',
        # Use composite Metazoan mitochondrial genetic code.
        '-gcmet',
        # Use Vertebrate mitochondrial genetic code.
        '-gcvert',
        # Use Invertebrate mitochondrial genetic code.
        '-gcinvert',
        # Use Yeast mitochondrial genetic code.
        '-gcyeast',
        # Use Mold/Protozoan/Coelenterate mitochondrial genetic code.
        '-gcprot',
        # Use Ciliate genetic code.
        '-gcciliate',
        # Use Echinoderm/Flatworm mitochondrial genetic code.
        '-gcflatworm',
        # Use Euplotid genetic code.
        '-gceuplot',
        # Use Bacterial/Plant Chloroplast genetic code.
        '-gcbact',
        # Use alternative Yeast genetic code.
        '-gcaltyeast',
        # Use Ascidian Mitochondrial genetic code.
        '-gcascid',
        # Use alternative Flatworm Mitochondrial genetic code.
        '-gcaltflat',
        # Use Blepharisma genetic code.
        '-gcblep',
        # Use Chlorophycean Mitochondrial genetic code.
        '-gcchloroph',
        # Use Trematode Mitochondrial genetic code.
        '-gctrem',
        # Use Scenedesmus obliquus Mitochondrial genetic code.
        '-gcscen',
        # Use Thraustochytrium Mitochondrial genetic code.
        # Individual modifications can be appended using
        '-gcthraust',
        # Do not search for mitochondrial TV replacement
        # loop tRNA genes. Only relevant if -mt used.
        '-tv',
        # Search for tRNA genes with introns in
        # anticodon loop with maximum length 3000
        # bases. Minimum intron length is 0 bases.
        # Ignored if -m is specified.
        '-i',
        # Same as -i, but allow tRNA genes with long
        # introns to overlap shorter tRNA genes.
        '-io',
        # Same as -i, but fix intron between positions
        # 37 and 38 on C-loop (one base after anticodon).
        '-if',
        # Same as -if and -io combined.
        '-ifo',
        # Same as -i, but search for tRNA genes with minimum intron
        # length 0 bases, and only report tRNA genes with minimum
        # intron length <min> bases.
        '-ir',
        # Assume that each sequence has a
        # topology. Search wraps around each end.
        # Default setting.
        '-c',
        # Assume that each sequence has a linear
        # topology. Search does not wrap.
        '-l',
        # Double. Search both strands of each
        # sequence. Default setting.
        '-d',
        # Single. Do not search the complementary
        # (antisense) strand of each sequence.
        '-s',
        '-s+',
        # Single complementary. Do not search the sense
        # strand of each sequence.
        '-sc',
        '-s-',
        # Use the stricter canonical 1-2 bp spacer1 and
        # 1 bp spacer2. Ignored if -mt set. Default is to
        # allow 3 bp spacer1 and 0-2 bp spacer2, which may
        # degrade selectivity.
        '-ss'
        #  Lower scoring thresholds to 95% of default levels.
        '-ps',
        #  Flag possible pseudogenes (score < 100 or tRNA anticodon
        #  loop <> 7 bases long). Note that genes with score < 100
        #  will not be detected or flagged if scoring thresholds are not
        #  also changed to below 100% (see -ps switch).
        '-rp',
        #  Print out primary sequence.
        '-seq',
        #  Show secondary structure of tRNA gene primary
        #  sequence with round brackets.
        '-br',
        #  Print out primary sequence in fasta format.
        '-fasta',
        #  Print out primary sequence in fasta format only
        #  (no secondary structure).
        '-fo',
        #  Same as -fo, with sequence and gene numbering in header.
        '-fon',
        #  Same as -fo, with no spaces in header.
        '-fos',
        #  Same as -fo, with sequence and gene numbering, but no spaces.
        '-fons',
        #  Display 4-base sequence on 3' end of astem
        #  regardless of predicted amino-acyl acceptor
        #  length.
        '-j',
        #  Allow some divergence of 3' amino-acyl acceptor
        #  sequence from NCCA.
        '-jr',
        #  Allow some divergence of 3' amino-acyl acceptor
        #  sequence from NCCA, and display 4 bases.
        '-jr4',
        #  Verbose. Prints out search progress
        #  to STDERR.
        '-v',
        #  Print out tRNA domain for tmRNA genes
        '-a',
        #  Print out genes in batch mode.
        #  For tRNA genes, output is in the form:
        #
        #  Sequence name
        #  N genes found
        #  1 tRNA-<species> [locus 1] <Apos> (nnn)
        #  i(<intron position>,<intron length>)
        #            .
        #            .
        #  N tRNA-<species> [Locus N] <Apos> (nnn)
        #  i(<intron position>,<intron length>)
        #
        #  N is the number of genes found
        #  <species> is the tRNA iso-acceptor species
        #  <Apos> is the tRNA anticodon relative position
        #  (nnn) is the tRNA anticodon base triplet
        #  i means the tRNA gene has a C-loop intron
        #
        #  For tmRNA genes, output is in the form:
        #
        #  n tmRNA(p) [Locus n] <tag offset>,<tag end offset>
        #  <tag peptide>
        #
        #  p means the tmRNA gene is permuted
       '-w']

       _parameters = {}
       _parameters.update({
           i: _get_parameter(
               ValuedParameter, i, Delimiter=' ', IsPath=True)
           for i in _valued_path_options})
       _parameters.update({
           i: _get_parameter(
               ValuedParameter, i, Delimiter=' ')
           for i in _valued_nonpath_options})
       _parameters.update({
           i: _get_parameter(FlagParameter, i)
           for i in _flag_options})

    def identify_features(in_fp, out_dir, prefix='aragorn', params=None):
        ''' Predict tRNAs and tmRNAs for the input file. '''
        return app(in_fp)

    def parse_output(res):
        ''' Parse gene prediction result from aragorn. '''
        pass
