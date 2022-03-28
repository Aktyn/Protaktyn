class Commands:
    exit = r"(koniec|zako[nń]cz|wy[lł][aą]cz) program"

    confirm = r"(tak|potwierdzam|potwierd[zź]|(za)?akceptuj)"
    reject = r"(nie|anuluj[eę]?|zaprzeczam|odrzuć|odrzucam)"

    exit_current_module = r"(zako[nń]cz|wy[lł][aą]cz|zamknij)( (obecny|aktywny))? modu[łl]"
    start_scoreboard_module = r"(za[lł]aduj|uruchom|w[lł][aą]cz) tablic[aąeę] punkt[oó]w"

    class SCOREBOARD:
        reset = r"(z?reset(uj)?|(wy)?zeruj) (punkty|wyniki|tablic[eę])"
        set_points = r".*(\s|^)([^\s]+)\s?(do|-)\s?([^\s]+).*"
