<?php
declare(strict_types=1);

/**
 * Round 2, step 2: observe whether the unmodified engine (app/scoring.php) can carry each externally
 * defined framework in probes/profiles_external.json as configuration. Run after
 * probes/predictions_external.json was written.
 *
 * Identical observation rules to probes/observe.php (O1 scheme, O2 scale, O3 factors); only the profile
 * and prediction files differ. No database and no institutional data are used.
 *
 * Usage: php probes/observe_external.php   → probes/observations_external.json
 */

$root = dirname(__DIR__);

final class AppDB
{
    public static function all(string $sql, array $params = []): array { return []; }
    public static function scalar(string $sql, array $params = []): int { return 1; }
}
function appCycleLocked(string $id): bool { return false; }
function sv(mixed $v): string { return is_scalar($v) ? (string) $v : ''; }
function iv(mixed $v): int { return is_numeric($v) ? (int) $v : 0; }
function av(mixed $v): array { return is_array($v) ? $v : []; }
function edpex(): array
{
    static $c = null;
    return $c ??= json_decode((string) file_get_contents(dirname(__DIR__) . '/config/edpex.json'), true);
}

require "$root/app/scoring.php";

$spec = json_decode((string) file_get_contents(__DIR__ . '/profiles_external.json'), true);
$predictions = [];
foreach (json_decode((string) file_get_contents(__DIR__ . '/predictions_external.json'), true)['predictions'] as $p) {
    $predictions[$p['id']] = $p['predicted'];
}

/** The EdPEx scale as the engine offers it, used for profiles that declare scale "edpex". */
function edpexScale(string $scheme): array
{
    return array_map(static fn(string $b): array => scoringChoices($scheme, $b), scoringBands($scheme));
}

function profileScale(array $side, string $scheme): array
{
    return $side['scale'] === 'edpex' ? edpexScale($scheme) : $side['scale'];
}

$rows = [];
foreach ($spec['profiles'] as $p) {
    $obs = ['O1_scheme' => true, 'O2_scale' => true, 'O3_factors' => true];
    $notes = [];
    foreach ($p['categories'] as [$n, $type]) {
        $sides = $type === 'results+process' ? ['results', 'process'] : [$type];
        $engineScheme = scoringScheme((int) $n);
        foreach ($sides as $side) {
            $want = $side === 'results' ? 'LeTCI' : 'ADLI';
            if (count($sides) > 1 || $engineScheme !== $want) {
                if ($obs['O1_scheme']) {
                    $notes[] = "category $n ($type): engine assigns $engineScheme";
                }
                $obs['O1_scheme'] = false;
            }
            if (edpexScale($want) !== profileScale($p[$side], $want)) {
                if ($obs['O2_scale']) {
                    $notes[] = "$side scale: engine offers " . count(edpexScale($want)) . ' bands, profile has '
                        . count(profileScale($p[$side], $want));
                }
                $obs['O2_scale'] = false;
            }
            $k = count($p[$side]['factors']);
            $top = $p[$side]['levels'] - 1;
            $bands = scoringBands($want);
            $topBand = end($bands);
            $topPct = max(scoringChoices($want, $topBand));
            $in = ['band' => $topBand, 'percent' => $topPct, 'strengths' => 'x', 'dims' => array_fill(0, $k, $top)];
            $acceptsTop = scoringValidate('probe', "$n.1", $want === 'LeTCI' ? 7 : 1, $in) === [];
            $in['dims'][0] = 0;
            $rejectsWeak = scoringValidate('probe', "$n.1", $want === 'LeTCI' ? 7 : 1, $in) !== [];
            if (!($acceptsTop && $rejectsWeak)) {
                if ($obs['O3_factors']) {
                    $notes[] = "$side factors ($k factors, {$p[$side]["levels"]} levels): top score "
                        . ($acceptsTop ? 'accepted' : 'rejected')
                        . ', weak factor ' . ($rejectsWeak ? 'rejected' : 'accepted');
                }
                $obs['O3_factors'] = false;
            }
        }
    }
    $observed = !in_array(false, $obs, true) ? 'configuration only' : 'dedicated module';
    $rows[] = ['id' => $p['id'], 'kind' => $p['kind'], 'observations' => $obs, 'notes' => $notes,
               'predicted' => $predictions[$p['id']], 'observed' => $observed,
               'prediction_correct' => $predictions[$p['id']] === $observed];
}
$lf = static fn(string $f): string => hash('sha256', str_replace("\r\n", "\n", (string) file_get_contents($f)));
$out = ['round' => 2,
        'engine_sha256_lf' => $lf("$root/app/scoring.php"),
        'predictions_sha256_lf' => $lf(__DIR__ . '/predictions_external.json'),
        'profiles' => $rows,
        'correct' => count(array_filter($rows, static fn($r) => $r['prediction_correct'])), 'total' => count($rows)];
file_put_contents(__DIR__ . '/observations_external.json',
    json_encode($out, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n");
foreach ($rows as $r) {
    printf("%-10s predicted %-20s observed %-20s %s  %s\n", $r['id'], $r['predicted'], $r['observed'],
        $r['prediction_correct'] ? 'OK  ' : 'MISS', implode('; ', $r['notes']));
}
printf("%d/%d predictions correct\n", $out['correct'], $out['total']);
