<?php
declare(strict_types=1);

/**
 * Step 2 of the prospective test: observe whether the unmodified engine (app/scoring.php) can carry each
 * profile in probes/profiles.json as configuration. Run after predictions.json was committed.
 *
 * The engine is loaded as is. Its database reads are replaced by in-memory stubs (no reference tables, so
 * bands come from config/edpex.json as in the engine's fallback path; one evidence record; cycle open).
 * No database and no institutional data are used.
 *
 * For a profile to be carried as configuration, all three observations must hold for every category:
 *   O1 scheme  - scoringScheme(n) gives the scheme the category is evaluated with (a category evaluated
 *                with both rubrics cannot be carried, because the engine assigns one scheme per category);
 *   O2 scale   - the bands and percentages the engine offers for that scheme equal the profile's scale;
 *   O3 factors - scoringValidate accepts a top score supported by the profile's factor ratings at their
 *                top level, and rejects the top score when one factor is rated at the bottom level.
 * Point totals are not used by any engine function, so they cannot be observed to fail.
 *
 * Usage: php probes/observe.php   → probes/observations.json
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

$spec = json_decode((string) file_get_contents(__DIR__ . '/profiles.json'), true);
$predictions = [];
foreach (json_decode((string) file_get_contents(__DIR__ . '/predictions.json'), true) as $p) {
    $predictions[$p['id']] = $p['predicted'];
}

function scale(array $side, array $spec): array
{
    return $side['scale'] === 'edpex' ? $spec['edpex_scale'] : $side['scale'];
}

function engineScale(string $scheme): array
{
    return array_map(static fn(string $b): array => scoringChoices($scheme, $b), scoringBands($scheme));
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
            $profileScale = scale($p[$side], $spec);
            if (engineScale($want) !== $profileScale) {
                if ($obs['O2_scale']) {
                    $notes[] = "$side scale: engine offers " . count(engineScale($want)) . ' bands, profile has ' . count($profileScale);
                }
                $obs['O2_scale'] = false;
            }
            // O3: top score with every factor at the profile's top level must be accepted,
            // and rejected when one factor sits at the bottom level
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
                    $notes[] = "$side factors ($k factors, {$p[$side]["levels"]} levels): top score " . ($acceptsTop ? 'accepted' : 'rejected');
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
$out = ['engine_sha256' => hash_file('sha256', "$root/app/scoring.php"),
        'predictions_sha256' => hash_file('sha256', __DIR__ . '/predictions.json'),
        'profiles' => $rows,
        'correct' => count(array_filter($rows, static fn($r) => $r['prediction_correct'])), 'total' => count($rows)];
file_put_contents(__DIR__ . '/observations.json', json_encode($out, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n");
foreach ($rows as $r) {
    printf("%-10s predicted %-20s observed %-20s %s  %s\n", $r['id'], $r['predicted'], $r['observed'],
           $r['prediction_correct'] ? 'OK  ' : 'MISS', implode('; ', $r['notes']));
}
printf("%d/%d predictions correct\n", $out['correct'], $out['total']);
