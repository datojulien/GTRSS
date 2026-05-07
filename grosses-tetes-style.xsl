<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  exclude-result-prefixes="itunes">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title><xsl:value-of select="/rss/channel/title"/></title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f6f8;
      --surface: #ffffff;
      --ink: #161616;
      --muted: #62615d;
      --line: #dde1e8;
      --red: #d6001c;
      --red-dark: #920016;
      --gold: #f0b429;
      --teal: #027d86;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }

    a {
      color: inherit;
    }

    .hero {
      background:
        linear-gradient(105deg, rgba(146,0,22,0.96), rgba(214,0,28,0.92) 48%, rgba(22,22,22,0.96)),
        var(--red);
      color: #ffffff;
      padding: 38px 24px 34px;
      border-bottom: 6px solid var(--gold);
    }

    .wrap {
      width: min(1080px, calc(100% - 32px));
      margin: 0 auto;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 172px;
      gap: 28px;
      align-items: center;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 5px 10px;
      border: 1px solid rgba(255,255,255,0.34);
      border-radius: 6px;
      background: rgba(255,255,255,0.12);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    h1 {
      margin: 14px 0 10px;
      font-size: 46px;
      line-height: 1;
      letter-spacing: 0;
    }

    .subtitle {
      max-width: 780px;
      margin: 0;
      color: rgba(255,255,255,0.9);
      font-size: 17px;
    }

    .hero-cover {
      width: 172px;
      aspect-ratio: 1;
      border-radius: 8px;
      object-fit: cover;
      border: 1px solid rgba(255,255,255,0.5);
      box-shadow: 0 16px 38px rgba(0,0,0,0.26);
      background: #ffffff;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      margin-top: 24px;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 8px;
      background: rgba(255,255,255,0.3);
    }

    .stat {
      min-width: 0;
      padding: 12px 14px;
      background: rgba(255,255,255,0.12);
    }

    .stat-label {
      display: block;
      color: rgba(255,255,255,0.72);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .stat-value {
      display: block;
      margin-top: 4px;
      overflow-wrap: anywhere;
      font-size: 15px;
      font-weight: 700;
    }

    .content {
      padding: 26px 0 58px;
    }

    .episodes {
      display: grid;
      gap: 14px;
    }

    .episode {
      display: grid;
      grid-template-columns: 112px minmax(0, 1fr);
      gap: 18px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: 0 8px 22px rgba(22,22,22,0.06);
    }

    .cover {
      width: 112px;
      aspect-ratio: 1;
      overflow: hidden;
      border-radius: 6px;
      background: #eef1f5;
      border: 1px solid var(--line);
    }

    .cover img {
      display: block;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .cover-fallback {
      display: grid;
      place-items: center;
      width: 100%;
      height: 100%;
      color: var(--red-dark);
      font-size: 28px;
      font-weight: 800;
    }

    .episode h2 {
      margin: 0;
      font-size: 21px;
      line-height: 1.22;
      letter-spacing: 0;
    }

    .episode h2 a {
      text-decoration: none;
    }

    .episode h2 a:hover {
      color: var(--red-dark);
      text-decoration: underline;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0 12px;
      color: var(--muted);
      font-size: 13px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      max-width: 100%;
      padding: 2px 8px;
      border-radius: 6px;
      background: #edf1f5;
      overflow-wrap: anywhere;
    }

    .duration {
      background: rgba(2,125,134,0.1);
      color: var(--teal);
      font-weight: 700;
    }

    .desc {
      margin: 0 0 14px;
      color: #3f3d39;
      font-size: 15px;
    }

    .desc p {
      margin: 0 0 8px;
    }

    audio {
      display: block;
      width: 100%;
      min-height: 40px;
    }

    .audio-link {
      display: inline-flex;
      margin-top: 10px;
      color: var(--red-dark);
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
    }

    .audio-link:hover {
      text-decoration: underline;
    }

    @media (max-width: 760px) {
      .hero {
        padding: 30px 16px 28px;
      }

      .wrap {
        width: min(100% - 24px, 1080px);
      }

      .hero-grid {
        grid-template-columns: 1fr;
      }

      .hero-cover {
        width: min(170px, 58vw);
      }

      .stats {
        grid-template-columns: 1fr;
      }

      .episode {
        grid-template-columns: 78px minmax(0, 1fr);
        gap: 12px;
        padding: 12px;
      }

      .cover {
        width: 78px;
      }

      .episode h2 {
        font-size: 18px;
      }

      h1 {
        font-size: 36px;
      }
    }

    @media (max-width: 460px) {
      .episode {
        grid-template-columns: 1fr;
      }

      .cover {
        width: 100%;
        max-height: 260px;
      }

      h1 {
        font-size: 30px;
      }
    }
  </style>
</head>

<body>
  <header class="hero">
    <div class="wrap">
      <div class="hero-grid">
        <div>
          <div class="badge">Flux RSS Grosses Têtes</div>
          <h1><xsl:value-of select="/rss/channel/title"/></h1>
          <p class="subtitle">
            <xsl:value-of select="/rss/channel/description"/>
          </p>
        </div>

        <xsl:if test="/rss/channel/itunes:image/@href">
          <img class="hero-cover" alt="">
            <xsl:attribute name="src">
              <xsl:value-of select="/rss/channel/itunes:image/@href"/>
            </xsl:attribute>
          </img>
        </xsl:if>
      </div>

      <div class="stats">
        <div class="stat">
          <span class="stat-label">Épisodes</span>
          <span class="stat-value">
            <xsl:value-of select="count(/rss/channel/item)"/>
          </span>
        </div>
        <div class="stat">
          <span class="stat-label">Auteur</span>
          <span class="stat-value">
            <xsl:value-of select="/rss/channel/itunes:author"/>
          </span>
        </div>
        <div class="stat">
          <span class="stat-label">Dernière MAJ</span>
          <span class="stat-value">
            <xsl:value-of select="/rss/channel/lastBuildDate"/>
          </span>
        </div>
      </div>
    </div>
  </header>

  <main class="content">
    <div class="wrap episodes">
      <xsl:for-each select="/rss/channel/item">
        <article class="episode">
          <div class="cover">
            <xsl:choose>
              <xsl:when test="itunes:image/@href">
                <img alt="">
                  <xsl:attribute name="src">
                    <xsl:value-of select="itunes:image/@href"/>
                  </xsl:attribute>
                </img>
              </xsl:when>
              <xsl:otherwise>
                <div class="cover-fallback">RTL</div>
              </xsl:otherwise>
            </xsl:choose>
          </div>

          <div>
            <h2>
              <a>
                <xsl:attribute name="href">
                  <xsl:value-of select="link"/>
                </xsl:attribute>
                <xsl:value-of select="title"/>
              </a>
            </h2>

            <div class="meta">
              <xsl:if test="pubDate">
                <span class="pill"><xsl:value-of select="pubDate"/></span>
              </xsl:if>
              <xsl:if test="itunes:author or author">
                <span class="pill">
                  <xsl:choose>
                    <xsl:when test="itunes:author">
                      <xsl:value-of select="itunes:author"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="author"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </span>
              </xsl:if>
              <xsl:if test="itunes:duration">
                <span class="pill duration"><xsl:value-of select="itunes:duration"/></span>
              </xsl:if>
            </div>

            <div class="desc">
              <xsl:value-of select="description" disable-output-escaping="yes"/>
            </div>

            <xsl:if test="enclosure/@url">
              <audio controls="controls" preload="none">
                <source>
                  <xsl:attribute name="src">
                    <xsl:value-of select="enclosure/@url"/>
                  </xsl:attribute>
                  <xsl:attribute name="type">
                    <xsl:value-of select="enclosure/@type"/>
                  </xsl:attribute>
                </source>
              </audio>
              <a class="audio-link">
                <xsl:attribute name="href">
                  <xsl:value-of select="enclosure/@url"/>
                </xsl:attribute>
                Ouvrir le fichier audio
              </a>
            </xsl:if>
          </div>
        </article>
      </xsl:for-each>
    </div>
  </main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
