<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title><xsl:value-of select="/rss/channel/title"/></title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #111111;
      --surface: #1b1b1f;
      --ink: #f5f5f5;
      --muted: #d8d2e6;
      --accent: #d3b9ff;
      --line: rgba(255,255,255,0.14);
      --focus: #ffd166;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.55;
    }

    a {
      color: inherit;
      text-decoration-thickness: 0.08em;
      text-underline-offset: 0.16em;
    }

    a:focus-visible,
    audio:focus-visible {
      outline: 3px solid var(--focus);
      outline-offset: 4px;
    }

    .hero {
      padding: 46px 20px 38px;
      background: #2d164f;
      border-bottom: 1px solid var(--line);
    }

    .wrap {
      width: min(950px, calc(100% - 32px));
      margin: 0 auto;
    }

    h1 {
      margin: 0 0 12px;
      font-size: clamp(30px, 6vw, 44px);
      line-height: 1.08;
      letter-spacing: 0;
    }

    .subtitle {
      max-width: 720px;
      margin: 0;
      color: var(--muted);
      font-size: 18px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      margin-bottom: 18px;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: rgba(255,255,255,0.08);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .rss-note {
      max-width: 720px;
      margin-top: 22px;
      padding: 14px 16px;
      border-radius: 8px;
      background: rgba(255,255,255,0.08);
      color: var(--muted);
      font-size: 14px;
    }

    .content {
      padding: 28px 0 58px;
    }

    .episodes {
      display: grid;
      gap: 16px;
    }

    .episode {
      display: grid;
      grid-template-columns: 120px minmax(0, 1fr);
      gap: 18px;
      padding: 18px;
      border-radius: 8px;
      background: var(--surface);
      border: 1px solid var(--line);
      box-shadow: 0 10px 28px rgba(0,0,0,0.24);
    }

    .cover {
      min-width: 0;
    }

    .cover img {
      display: block;
      width: 120px;
      aspect-ratio: 1;
      object-fit: cover;
      border-radius: 6px;
      background: #333333;
      border: 1px solid var(--line);
    }

    .episode h2 {
      margin: 0 0 8px;
      font-size: 22px;
      line-height: 1.22;
      letter-spacing: 0;
    }

    .episode h2 a {
      color: #ffffff;
    }

    .date {
      color: var(--accent);
      font-size: 14px;
      margin-bottom: 10px;
    }

    .desc {
      color: #e6e1ef;
      margin-bottom: 14px;
    }

    audio {
      display: block;
      width: 100%;
      min-height: 40px;
      margin-top: 8px;
    }

    .audio-link {
      display: inline-flex;
      margin-top: 10px;
      color: var(--accent);
      font-size: 14px;
      font-weight: 700;
    }

    @media (max-width: 650px) {
      .hero {
        padding: 34px 16px 30px;
      }

      .wrap {
        width: min(100% - 24px, 950px);
      }

      .episode {
        grid-template-columns: 1fr;
        padding: 14px;
      }

      .cover img {
        width: 100%;
        max-height: 280px;
      }
    }
  </style>
</head>

<body>
  <header class="hero">
    <div class="wrap">
      <div class="badge">RSS personnel</div>
      <h1><xsl:value-of select="/rss/channel/title"/></h1>
      <p class="subtitle">
        <xsl:value-of select="/rss/channel/description"/>
      </p>
      <div class="rss-note">
        This is a podcast RSS feed. Copy this URL into a podcast app to subscribe.
      </div>
    </div>
  </header>

  <main class="content">
    <div class="wrap episodes">
      <xsl:for-each select="/rss/channel/item">
        <article class="episode">
          <div class="cover">
            <xsl:variable
              name="contentImage"
              select="substring-before(substring-after(content:encoded, '&lt;img src=&quot;'), '&quot;')"
            />
            <xsl:variable name="coverImage">
              <xsl:choose>
                <xsl:when test="itunes:image/@href">
                  <xsl:value-of select="itunes:image/@href"/>
                </xsl:when>
                <xsl:when test="$contentImage != ''">
                  <xsl:value-of select="$contentImage"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="/rss/channel/image/url"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:variable>

            <xsl:if test="$coverImage != ''">
              <img>
                <xsl:attribute name="src">
                  <xsl:value-of select="$coverImage"/>
                </xsl:attribute>
                <xsl:attribute name="alt">
                  <xsl:value-of select="title"/>
                </xsl:attribute>
              </img>
            </xsl:if>
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

            <div class="date">
              <xsl:value-of select="pubDate"/>
            </div>

            <div class="desc">
              <xsl:value-of select="description"/>
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
