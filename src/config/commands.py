class Commands:
    exit = r"(koniec|zako[nń]cz|wy[lł][aą]cz) program"

    confirm = r"(tak|potwierdzam|potwierd[zź]|(za)?akceptuj)"
    reject = r"(nie|anuluj[eę]?|zaprzeczam|odrzuć|odrzucam)"

    exit_current_module = r"(zako[nń]cz|wy[lł][aą]cz|zamknij)( (obecny|aktywny))? modu[łl]"

    class SCOREBOARD:
        start_module = r"(za[lł]aduj|uruchom|w[lł][aą]cz|rozpocznij|zacznij) tablic[aąeęy] punkt[oó]w[aą]"
        reset = r"(z?reset(uj)?|(wy)?zeruj) (punkty|wyniki|tablic[eę])"
        set_points = r".*(\s|^)([^\s]+)\s?(do|-)\s?([^\s]+).*"
        point_for_left_player = r"(punkt (dla|do|ma) lew(y|ego)|wygra[lł] lew[yo])"
        point_for_right_player = r"(punkt (dla|do|ma) praw(y|ego)|wygra[lł] praw[yo])"
        easter_egg = r"(jajko|jajo|jajco)"

    class ROBOT:
        start_module = r"(za[lł]aduj|uruchom|w[lł][aą]cz|rozpocznij|zacznij) (modu[łl] )?robota?"
