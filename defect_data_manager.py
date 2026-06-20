from ipdds.data_store import DefectDataStore


class DefectDataManager(DefectDataStore):
    """Backward-compatible alias for the refactored data store."""

    def save_defect_data(self):
        self.save()

    def get_dirty_in_timerange(self, start_ts, end_ts, freq):
        return self.get_defect_counts("dirty", start_ts, end_ts, freq)

    def get_scratch_in_timerange(self, start_ts, end_ts, freq):
        return self.get_defect_counts("scratch", start_ts, end_ts, freq)
