class Commands:
    exit = r"(koniec|zako[nń]cz|wy[lł][aą]cz) program"

    confirm = r"(tak|potwierdzam|potwierd[zź]|(za)?akceptuj)"
    reject = r"(nie|anuluj[eę]?|zaprzeczam|odrzuć|odrzucam)"

    exit_current_module = r"(zako[nń]cz|wy[lł][aą]cz|zamknij)( (obecny|aktywny))? modu[łl]"

    class SCOREBOARD:
        start_module = r"(za[lł]aduj|uruchom|w[lł][aą]cz|rozpocznij|zacznij) tablic[aąeę] punkt[oó]w"
        reset = r"(z?reset(uj)?|(wy)?zeruj) (punkty|wyniki|tablic[eę])"
        set_points = r".*(\s|^)([^\s]+)\s?(do|-)\s?([^\s]+).*"
        easter_egg = r"(jajko|jajo|jajco)"

    class ROBOT:
        start_module = r"(za[lł]aduj|uruchom|w[lł][aą]cz|rozpocznij|zacznij) (modu[łl] )?robota?"
