import progressbar as pb

def progress_bar(description, maxval):
    widgets = [description, pb.Percentage(), ' ',
                pb.Bar(marker=pb.RotatingMarker()), ' ', pb.ETA()]
    pbar = pb.ProgressBar(widgets=widgets, maxval=maxval).start()
    pbar.update(0)
    return pbar
